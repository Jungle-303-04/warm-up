"""소스 인덱싱 유스케이스.

소스를 파일/문단 단위로 청킹 → 임베딩 → ChunkStore에 저장하고, 매 단계마다
진행 레지스트리를 갱신한다. 외부 키 없이 동작해야 하므로 임베딩 클라이언트는
기본적으로 결정론적(deterministic)이며, repo clone/LLM 호출은 하지 않는다.

지원 언어(.py/.md)만 repo_rag 청커로 인덱싱하고, 그 외 repo 파일은 skip한다.
md/text/pdf 소스는 각각 마크다운 청커/텍스트 분할기로 처리하고, url 소스는
인덱싱 대상이 아니다(즉시 done, total_files 0).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TYPE_CHECKING
from uuid import uuid4

from app.notebooks.domain.chunk_records import NotebookChunk
from app.notebooks.domain.indexing_progress import (
    FileProgress,
    IndexProgress,
    IndexProgressRegistry,
)
from app.notebooks.domain.ports import ChunkStore, NotebookStore
from app.notebooks.domain.records import SourceRecord
from app.repo_rag.domain.ports import EmbeddingClient
from fastapi import Depends
from app.notebooks.dependencies import (
    get_notebook_store,
    get_chunk_store,
    get_embedding_client,
    get_progress_registry_dep,
)

if TYPE_CHECKING:
    from app.repository_source.infrastructure.repo_sync import RepoSyncService


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


def get_id_factory() -> Callable[[], str]:
    return lambda: uuid4().hex


@dataclass(slots=True)
class _FileChunks:
    """한 "파일"(또는 단일 텍스트 단위)에서 나온 청크 텍스트 묶음."""

    path: str
    language: str | None
    supported: bool
    texts: list[str]


@dataclass(slots=True)
class IndexingService:
    store: NotebookStore = Depends(get_notebook_store)
    chunk_store: ChunkStore = Depends(get_chunk_store)
    embedder: EmbeddingClient = Depends(get_embedding_client)
    registry: IndexProgressRegistry = Depends(get_progress_registry_dep)
    clock: Callable[[], datetime] = Depends(get_clock)
    id_factory: Callable[[], str] = Depends(get_id_factory)

    def __post_init__(self) -> None:
        from fastapi.params import Depends as DependsClass
        if isinstance(self.clock, DependsClass):
            self.clock = self.clock.dependency()
        if isinstance(self.id_factory, DependsClass):
            self.id_factory = self.id_factory.dependency()
    # repo 재풀링(재클론)용. None이면 재풀링 없이 기존 스냅샷으로 인덱싱한다.
    # 헥사고날 경계: NotebookService와 동일한 RepoSyncService 포트를 주입받는다.
    repo_sync: "Any | None" = Depends(lambda: __import__('app.repository_source.infrastructure.repo_sync', fromlist=['RepoSyncService']).RepoSyncService())

    def register(self, source: SourceRecord) -> None:
        """소스 생성 직후 큐 등록(BackgroundTasks 실행 전 호출)."""
        self.registry.register(source.id, source.notebook_id)

    def index_source(
        self, notebook_id: str, source_id: str, *, resync_repo: bool = False
    ) -> None:
        """소스를 실제로 인덱싱한다(BackgroundTasks/스레드에서 호출).

        resync_repo=True이고 repo 소스이면, 인덱싱 전에 저장소를 재클론하여
        repo_snapshot을 최신 스냅샷으로 갱신한다(= "최신화"). 재클론 실패 시
        기존 스냅샷으로 폴백하고 progress.error에 사유를 남긴다.
        """
        try:
            source = self.store.get_source(notebook_id, source_id)
        except KeyError:
            self.registry.update(source_id, _fail("소스를 찾을 수 없습니다"))
            return

        resync_error: str | None = None
        if resync_repo and source.kind == "repo":
            source, resync_error = self._resync_repo(source)

        # 재인덱싱 대비: 기존 청크 정리.
        self.chunk_store.delete_by_source(source_id)

        try:
            file_chunks = _plan_files(source)
        except Exception as exc:
            self.registry.update(source_id, _fail(str(exc)))
            return

        self.registry.update(source_id, _start(file_chunks))

        if not file_chunks:
            # url 소스 등: 인덱싱 대상 없음 → 즉시 done.
            self.registry.update(source_id, _finish(self.clock()))
            return

        created_at = self.clock()
        for file in file_chunks:
            self.registry.update(source_id, _mark_file_indexing(file.path))
            if not file.supported or not file.texts:
                self.registry.update(source_id, _mark_file_skipped(file.path))
                continue
            try:
                chunks = self._build_chunks(source, file, created_at)
                self.chunk_store.add_many(chunks)
            except Exception as exc:
                self.registry.update(source_id, _fail(str(exc)))
                return
            self.registry.update(source_id, _mark_file_done(file.path, len(chunks)))

        self.registry.update(source_id, _finish(self.clock()))
        # 재풀링은 실패해도 기존 스냅샷으로 인덱싱은 완료(done)시키되, 사유는 남긴다.
        if resync_error is not None:
            self.registry.update(source_id, _set_error(resync_error))

    def _resync_repo(self, source: SourceRecord) -> tuple[SourceRecord, str | None]:
        """repo 소스를 재클론하여 최신 스냅샷으로 갱신한다.

        성공: 갱신된 SourceRecord와 None을 돌려준다(저장소에도 영속).
        실패: 기존 SourceRecord와 에러 메시지를 돌려준다(폴백).
        repo_sync가 주입되지 않았거나 repository_url이 없으면 재풀링을 건너뛴다.
        """
        if self.repo_sync is None or not source.repository_url:
            return source, None

        # 무거운 의존성은 함수 내 지연 import.
        from subprocess import CalledProcessError

        from app.pipeline.api.schemas import DEFAULT_BRANCH, PipelineRequest

        try:
            snapshot = self.repo_sync.sync(
                PipelineRequest(
                    repository=source.title,
                    repository_url=source.repository_url,
                    branch=source.branch or DEFAULT_BRANCH,
                )
            )
        except (ValueError, CalledProcessError) as exc:
            # 재클론 실패: 기존 스냅샷으로 폴백.
            return source, f"저장소 재동기화에 실패해 기존 스냅샷을 사용합니다: {exc}"

        source.repo_snapshot = [
            {"path": file.path, "content": file.content} for file in snapshot.files
        ]
        source.branch = snapshot.branch or source.branch
        # 최신 스냅샷을 저장소에 영속(merge upsert).
        self.store.add_source(source)
        return source, None

    def reindex_source(self, notebook_id: str, source_id: str) -> None:
        try:
            source = self.store.get_source(notebook_id, source_id)
        except KeyError:
            return
        self.register(source)
        # repo 소스면 재풀링(최신화) 포함.
        self.index_source(notebook_id, source_id, resync_repo=True)

    def cleanup_source(self, source_id: str) -> None:
        """소스 삭제 시 청크와 진행 상태를 정리한다."""
        self.chunk_store.delete_by_source(source_id)
        self.registry.remove(source_id)

    def _build_chunks(
        self,
        source: SourceRecord,
        file: _FileChunks,
        created_at: datetime,
    ) -> list[NotebookChunk]:
        embeddings = self.embedder.embed_documents(file.texts)
        chunks: list[NotebookChunk] = []
        for index, (text, embedding) in enumerate(zip(file.texts, embeddings, strict=False)):
            chunks.append(
                NotebookChunk(
                    id=self.id_factory(),
                    notebook_id=source.notebook_id,
                    source_id=source.id,
                    chunk_index=index,
                    text=text,
                    file_path=file.path if file.path != _TEXT_UNIT else None,
                    language=file.language,
                    embedding=list(embedding),
                    created_at=created_at,
                )
            )
        return chunks


# --- 소스별 청킹 계획 ---

_TEXT_UNIT = "__text__"


def _plan_files(source: SourceRecord) -> list[_FileChunks]:
    if source.kind == "repo":
        return _plan_repo(source)
    if source.kind == "md":
        return _plan_markdown(source)
    if source.kind in ("text", "pdf"):
        return _plan_plain_text(source)
    # url 등: 인덱싱 대상 아님.
    return []


def _plan_repo(source: SourceRecord) -> list[_FileChunks]:
    from app.repo_rag.domain.chunk_identity import FileContext
    from app.repo_rag.domain.chunking import DEFAULT_CHUNKER_REGISTRY, detect_language

    snapshot = source.repo_snapshot or []
    files: list[_FileChunks] = []
    for entry in snapshot:
        path = str(entry.get("path") or "")
        content = entry.get("content")
        if not path:
            continue
        language = detect_language(path)
        if language is None:
            files.append(_FileChunks(path=path, language=None, supported=False, texts=[]))
            continue
        if not isinstance(content, str) or not content.strip():
            files.append(_FileChunks(path=path, language=language, supported=True, texts=[]))
            continue
        chunker = DEFAULT_CHUNKER_REGISTRY.get(language)
        if chunker is None:
            files.append(_FileChunks(path=path, language=None, supported=False, texts=[]))
            continue
        file_context = FileContext(
            repository=source.title,
            path=path,
            commit_sha=source.branch or "HEAD",
            content_hash="",
            content=content,
            language=language,
        )
        drafts = chunker.build_chunks(file_context)
        texts = [draft.text for draft in drafts if draft.text.strip()]
        files.append(
            _FileChunks(path=path, language=language, supported=True, texts=texts)
        )
    return files


def _plan_markdown(source: SourceRecord) -> list[_FileChunks]:
    from app.repo_rag.domain.chunk_identity import FileContext
    from app.repo_rag.domain.chunking import DEFAULT_CHUNKER_REGISTRY

    content = source.content or ""
    if not content.strip():
        return []
    chunker = DEFAULT_CHUNKER_REGISTRY.get("markdown")
    file_context = FileContext(
        repository=source.title,
        path=source.title,
        commit_sha="HEAD",
        content_hash="",
        content=content,
        language="markdown",
    )
    drafts = chunker.build_chunks(file_context) if chunker else []
    texts = [draft.text for draft in drafts if draft.text.strip()]
    return [
        _FileChunks(path=source.title, language="markdown", supported=True, texts=texts)
    ]


def _plan_plain_text(source: SourceRecord) -> list[_FileChunks]:
    from app.repo_rag.domain.text_splitter import DEFAULT_TEXT_SPLITTER_SERVICE

    content = source.content or ""
    if not content.strip():
        return []
    texts = DEFAULT_TEXT_SPLITTER_SERVICE.split(content)
    return [
        _FileChunks(path=_TEXT_UNIT, language="text", supported=True, texts=texts)
    ]


# --- 진행 레지스트리 변형(mutate) 헬퍼 ---


def _start(files: list[_FileChunks]):
    def mutate(progress: IndexProgress) -> None:
        progress.status = "running"
        progress.total_files = len(files)
        progress.processed_files = 0
        progress.skipped_files = 0
        progress.total_chunks = sum(len(file.texts) for file in files if file.supported)
        progress.indexed_chunks = 0
        progress.error = None
        progress.files = [
            FileProgress(
                path=file.path,
                language=file.language,
                supported=file.supported,
                status="queued",
            )
            for file in files
        ]

    return mutate


def _mark_file_indexing(path: str):
    def mutate(progress: IndexProgress) -> None:
        for file in progress.files:
            if file.path == path:
                file.status = "indexing"

    return mutate


def _mark_file_done(path: str, chunks: int):
    def mutate(progress: IndexProgress) -> None:
        for file in progress.files:
            if file.path == path:
                file.status = "done"
                file.chunks = chunks
        progress.processed_files += 1
        progress.indexed_chunks += chunks

    return mutate


def _mark_file_skipped(path: str):
    def mutate(progress: IndexProgress) -> None:
        for file in progress.files:
            if file.path == path:
                file.status = "skipped"
        progress.processed_files += 1
        progress.skipped_files += 1

    return mutate


def _finish(synced_at: datetime):
    def mutate(progress: IndexProgress) -> None:
        progress.status = "done"
        # 인덱싱이 done으로 끝난 순간 = 마지막으로 DB를 최신화한 시각.
        progress.last_synced_at = synced_at

    return mutate


def _fail(error: str):
    def mutate(progress: IndexProgress) -> None:
        progress.status = "failed"
        progress.error = error

    return mutate


def _set_error(error: str):
    """상태는 그대로 두고 error 사유만 기록(예: 재풀링 실패 후 폴백 완료)."""

    def mutate(progress: IndexProgress) -> None:
        progress.error = error

    return mutate
