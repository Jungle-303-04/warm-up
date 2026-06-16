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


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class _FileChunks:
    """한 "파일"(또는 단일 텍스트 단위)에서 나온 청크 텍스트 묶음."""

    path: str
    language: str | None
    supported: bool
    texts: list[str]


@dataclass(slots=True)
class IndexingService:
    store: NotebookStore
    chunk_store: ChunkStore
    embedder: EmbeddingClient
    registry: IndexProgressRegistry
    clock: Callable[[], datetime] = _utcnow
    id_factory: Callable[[], str] = _new_id

    def register(self, source: SourceRecord) -> None:
        """소스 생성 직후 큐 등록(BackgroundTasks 실행 전 호출)."""
        self.registry.register(source.id, source.notebook_id)

    def index_source(self, notebook_id: str, source_id: str) -> None:
        """소스를 실제로 인덱싱한다(BackgroundTasks/스레드에서 호출)."""
        try:
            source = self.store.get_source(notebook_id, source_id)
        except KeyError:
            self.registry.update(source_id, _fail("소스를 찾을 수 없습니다"))
            return

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
            self.registry.update(source_id, _finish())
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

        self.registry.update(source_id, _finish())

    def reindex_source(self, notebook_id: str, source_id: str) -> None:
        try:
            source = self.store.get_source(notebook_id, source_id)
        except KeyError:
            return
        self.register(source)
        self.index_source(notebook_id, source_id)

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


def _finish():
    def mutate(progress: IndexProgress) -> None:
        progress.status = "done"

    return mutate


def _fail(error: str):
    def mutate(progress: IndexProgress) -> None:
        progress.status = "failed"
        progress.error = error

    return mutate
