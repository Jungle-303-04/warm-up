"""소스 인덱싱 유스케이스.

소스를 파일/문단 단위로 청킹 → 임베딩 → ChunkStore에 저장하고, 매 단계마다
진행 레지스트리를 갱신한다. 외부 키 없이 동작해야 하므로 임베딩 클라이언트는
기본적으로 결정론적(deterministic)이며, repo clone/LLM 호출은 하지 않는다.

repo 파일과 md/text/pdf/url 소스를 자료형별 청커로 처리한다. URL 소스는
SSRF 방어가 들어간 LinkFetcher 포트로 본문 후보를 가져와 정제 후 색인한다.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from app.notebooks.domain.chunk_records import NotebookChunk
from app.notebooks.domain.indexing_progress import (
    FileProgress,
    IndexProgress,
)
from app.notebooks.domain.ports import ChunkStore, IndexingProgressStore, NotebookStore
from app.notebooks.domain.records import SourceRecord
from app.repo_rag.domain.identity import hash_text
from app.repo_rag.domain.ports import EmbeddingClient
from app.repository_source.infrastructure.repo_sync import RepoSyncService

if TYPE_CHECKING:
    from app.link_metadata.domain.ports import LinkFetcher


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


def get_id_factory() -> Callable[[], str]:
    return lambda: uuid4().hex


@dataclass(slots=True)
class _PlannedChunk:
    text: str
    format: str | None = None
    heading_path: list[str] | None = None
    page: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    content_hash: str | None = None
    parent_chunk_id: str | None = None
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None


@dataclass(slots=True)
class _FileChunks:
    """한 "파일"(또는 단일 텍스트 단위)에서 나온 청크 묶음."""

    path: str
    language: str | None
    supported: bool
    chunks: list[_PlannedChunk]


@dataclass(slots=True)
class IndexingService:
    store: NotebookStore
    chunk_store: ChunkStore
    embedder: EmbeddingClient
    registry: IndexingProgressStore
    clock: Any = field(default_factory=get_clock)
    id_factory: Any = field(default_factory=get_id_factory)
    # repo 재풀링(재클론)용. None이면 재풀링 없이 기존 스냅샷으로 인덱싱한다.
    # 헥사고날 경계: NotebookService와 동일한 RepoSyncService 포트를 주입받는다.
    repo_sync: Any | None = field(default_factory=RepoSyncService)
    # URL 소스 본문 수집용. None이면 네트워크 호출 없이 URL 색인을 건너뛴다.
    url_fetcher: "LinkFetcher | None" = None

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
            file_chunks = _plan_files(source, self.url_fetcher)
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
            if not file.supported or not file.chunks:
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

        from app.pipeline.router import DEFAULT_BRANCH, PipelineRequest

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
        source.repo_commits = [commit.model_dump() for commit in snapshot.commits]
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
        texts = [chunk.text for chunk in file.chunks]
        embeddings = self.embedder.embed_documents(texts)
        chunks: list[NotebookChunk] = []
        for index, (planned, embedding) in enumerate(
            zip(file.chunks, embeddings, strict=False)
        ):
            chunks.append(
                NotebookChunk(
                    id=self.id_factory(),
                    notebook_id=source.notebook_id,
                    source_id=source.id,
                    chunk_index=index,
                    text=planned.text,
                    file_path=file.path if file.path != _TEXT_UNIT else None,
                    language=file.language,
                    format=planned.format or file.language,
                    heading_path=planned.heading_path,
                    page=planned.page,
                    start_line=planned.start_line,
                    end_line=planned.end_line,
                    start_offset=planned.start_offset,
                    end_offset=planned.end_offset,
                    content_hash=planned.content_hash,
                    parent_chunk_id=planned.parent_chunk_id,
                    prev_chunk_id=planned.prev_chunk_id,
                    next_chunk_id=planned.next_chunk_id,
                    embedding=list(embedding),
                    created_at=created_at,
                )
            )
        for index, chunk in enumerate(chunks):
            if chunk.prev_chunk_id is None and index > 0:
                chunk.prev_chunk_id = chunks[index - 1].id
            if chunk.next_chunk_id is None and index + 1 < len(chunks):
                chunk.next_chunk_id = chunks[index + 1].id
        return chunks


# --- 소스별 청킹 계획 ---

_TEXT_UNIT = "__text__"


def _plan_files(
    source: SourceRecord,
    url_fetcher: "LinkFetcher | None" = None,
) -> list[_FileChunks]:
    if source.kind == "repo":
        return _plan_repo(source)
    if source.kind == "md":
        return _plan_markdown(source)
    if source.kind in ("text", "pdf"):
        return _plan_plain_text(source)
    if source.kind == "url":
        return _plan_url(source, url_fetcher)
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
            files.append(_FileChunks(path=path, language=None, supported=False, chunks=[]))
            continue
        if not isinstance(content, str) or not content.strip():
            files.append(_FileChunks(path=path, language=language, supported=True, chunks=[]))
            continue
        chunker = DEFAULT_CHUNKER_REGISTRY.get(language)
        if chunker is None:
            files.append(_FileChunks(path=path, language=None, supported=False, chunks=[]))
            continue
        content_hash = hash_text(content)
        file_context = FileContext(
            repository=source.title,
            path=path,
            commit_sha=source.branch or "HEAD",
            content_hash=content_hash,
            content=content,
            language=language,
        )
        drafts = chunker.build_chunks(file_context)
        planned = [_planned_from_draft(draft, language, content_hash) for draft in drafts]
        files.append(
            _FileChunks(path=path, language=language, supported=True, chunks=planned)
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
        content_hash=hash_text(content),
        content=content,
        language="markdown",
    )
    drafts = chunker.build_chunks(file_context) if chunker else []
    planned = [_planned_from_draft(draft, "markdown", file_context.content_hash) for draft in drafts]
    return [
        _FileChunks(path=source.title, language="markdown", supported=True, chunks=planned)
    ]


def _plan_plain_text(source: SourceRecord) -> list[_FileChunks]:
    from app.repo_rag.domain.chunk_identity import FileContext
    from app.repo_rag.domain.chunking import DEFAULT_CHUNKER_REGISTRY

    content = source.content or ""
    if not content.strip():
        return []
    language = "pdf" if source.kind == "pdf" else "text"
    chunker = DEFAULT_CHUNKER_REGISTRY.get(language)
    content_hash = hash_text(content)
    file_context = FileContext(
        repository=source.title,
        path=source.title,
        commit_sha="HEAD",
        content_hash=content_hash,
        content=content,
        language=language,
    )
    drafts = chunker.build_chunks(file_context) if chunker else []
    planned = [_planned_from_draft(draft, language, content_hash) for draft in drafts]
    return [
        _FileChunks(path=_TEXT_UNIT, language=language, supported=True, chunks=planned)
    ]


def _plan_url(
    source: SourceRecord,
    url_fetcher: "LinkFetcher | None",
) -> list[_FileChunks]:
    if source.url is None or not source.url.strip() or url_fetcher is None:
        return []

    from app.notebooks.application.url_content import UrlContentExtractor
    from app.repo_rag.domain.chunk_identity import FileContext
    from app.repo_rag.domain.chunking import DEFAULT_CHUNKER_REGISTRY

    document = UrlContentExtractor(url_fetcher).fetch_document(
        source.url,
        fallback_title=source.title,
    )
    if document is None:
        return []

    content_hash = hash_text(document.text)
    chunker = DEFAULT_CHUNKER_REGISTRY.get("text")
    file_context = FileContext(
        repository=source.title,
        path=document.url,
        commit_sha="HEAD",
        content_hash=content_hash,
        content=document.text,
        language="text",
        source_type="url",
    )
    drafts = chunker.build_chunks(file_context) if chunker else []
    planned = [_planned_from_draft(draft, "url", content_hash) for draft in drafts]
    return [
        _FileChunks(
            path=document.url,
            language="url",
            supported=True,
            chunks=planned,
        )
    ]


# --- 진행 레지스트리 변형(mutate) 헬퍼 ---


def _start(files: list[_FileChunks]):
    def mutate(progress: IndexProgress) -> None:
        progress.status = "running"
        progress.total_files = len(files)
        progress.processed_files = 0
        progress.skipped_files = 0
        progress.total_chunks = sum(len(file.chunks) for file in files if file.supported)
        progress.indexed_chunks = 0
        progress.error = None
        progress.content_hash = _files_content_hash(files)
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


def _planned_from_draft(
    draft,
    format: str,
    content_hash: str,
) -> _PlannedChunk:
    return _PlannedChunk(
        text=draft.text,
        format=format,
        heading_path=draft.heading_path,
        page=draft.page,
        start_line=draft.start_line,
        end_line=draft.end_line,
        start_offset=draft.start_offset,
        end_offset=draft.end_offset,
        content_hash=content_hash,
        parent_chunk_id=draft.parent_chunk_id,
        prev_chunk_id=draft.prev_chunk_id,
        next_chunk_id=draft.next_chunk_id,
    )


def _files_content_hash(files: list[_FileChunks]) -> str | None:
    parts = [
        f"{file.path}:{chunk.content_hash or hash_text(chunk.text)}"
        for file in files
        for chunk in file.chunks
    ]
    if not parts:
        return None
    return hash_text("\n".join(parts))


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
