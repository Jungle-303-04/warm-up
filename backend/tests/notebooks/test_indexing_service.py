"""인덱싱 서비스 테스트(in-memory + deterministic 임베딩).

repo 소스에서 .py/.md만 인덱싱하고 그 외 파일은 skip하며, 완료 시 진행 상태가
done/100%가 되는지 검증한다. 네트워크/clone/LLM 호출은 하지 않는다.
"""

from datetime import UTC, datetime
from itertools import count

from app.notebooks.application.indexing_service import IndexingService
from app.notebooks.application.service import NotebookService
from app.notebooks.domain.indexing_progress import IndexProgressRegistry
from app.notebooks.domain.records import SourceRecord
from app.notebooks.infrastructure.in_memory_chunk_store import InMemoryChunkStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore
from app.repo_rag.infrastructure.embeddings import DeterministicEmbeddingClient

FIXED_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _build():
    counter = count(1)
    store = InMemoryNotebookStore()
    chunk_store = InMemoryChunkStore()
    registry = IndexProgressRegistry()
    notebook_service = NotebookService(
        store=store,
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"src-{next(counter)}",
    )
    indexing = IndexingService(
        store=store,
        chunk_store=chunk_store,
        embedder=DeterministicEmbeddingClient(dimension=64),
        registry=registry,
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"chunk-{next(counter)}",
    )
    return notebook_service, indexing, chunk_store, registry


def test_repo_indexes_py_md_and_skips_unsupported() -> None:
    notebook_service, indexing, chunk_store, registry = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    repo = SourceRecord(
        id="repo-1",
        notebook_id=notebook.id,
        kind="repo",
        title="team/api",
        repository_url="https://github.com/team/api",
        branch="main",
        repo_snapshot=[
            {"path": "app/main.py", "content": "def run():\n    return 1\n"},
            {"path": "docs/guide.md", "content": "# 안내\n\n사용법 설명"},
            {"path": "assets/logo.png", "content": "binary"},
            {"path": "data.json", "content": "{}"},
        ],
        created_at=FIXED_NOW,
    )
    notebook_service.store.add_source(repo)

    indexing.register(repo)
    indexing.index_source(notebook.id, repo.id)

    view = registry.get(repo.id)
    assert view is not None
    assert view["status"] == "done"
    assert view["percent"] == 100
    assert view["total_files"] == 4
    assert view["processed_files"] == 4
    assert view["skipped_files"] == 2  # png, json 미지원
    assert view["indexed_chunks"] > 0

    statuses = {file["path"]: file["status"] for file in view["files"]}
    assert statuses["app/main.py"] == "done"
    assert statuses["docs/guide.md"] == "done"
    assert statuses["assets/logo.png"] == "skipped"
    assert statuses["data.json"] == "skipped"

    languages = {file["path"]: file["language"] for file in view["files"]}
    assert languages["app/main.py"] == "python"
    assert languages["docs/guide.md"] == "markdown"
    assert languages["assets/logo.png"] is None

    # 실제 청크가 저장됐고, 미지원 파일 경로는 청크에 없어야 한다.
    assert chunk_store.count_by_source(repo.id) == view["indexed_chunks"]


def test_md_source_indexes_and_completes() -> None:
    notebook_service, indexing, chunk_store, registry = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    source = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="# 인증\n\n세션 토큰 만료 검증\n\n## 추가\n\n쿠키 저장",
    )

    indexing.register(source)
    indexing.index_source(notebook.id, source.id)

    view = registry.get(source.id)
    assert view["status"] == "done"
    assert view["percent"] == 100
    assert view["total_files"] == 1
    assert chunk_store.count_by_source(source.id) > 0


def test_text_source_indexes_with_text_language() -> None:
    notebook_service, indexing, chunk_store, registry = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    source = notebook_service.add_source(
        notebook.id,
        kind="text",
        title="notes.txt",
        content="문단 하나입니다.\n\n" + ("길고 반복되는 문장. " * 80),
    )

    indexing.register(source)
    indexing.index_source(notebook.id, source.id)

    view = registry.get(source.id)
    assert view["status"] == "done"
    assert chunk_store.count_by_source(source.id) > 0
    # text 소스 청크는 file_path 없이 language="text".
    hits = chunk_store.search(
        notebook.id,
        query_embedding=None,
        query_text="반복되는 문장",
        source_ids=[source.id],
        top_k=3,
    )
    assert hits
    assert hits[0].chunk.language == "text"
    assert hits[0].chunk.file_path is None


def test_url_source_done_with_zero_files() -> None:
    notebook_service, indexing, chunk_store, registry = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    source = notebook_service.add_source(
        notebook.id,
        kind="url",
        title="link",
        url="https://example.com",
    )

    indexing.register(source)
    indexing.index_source(notebook.id, source.id)

    view = registry.get(source.id)
    assert view["status"] == "done"
    assert view["total_files"] == 0
    assert view["percent"] == 100
    assert chunk_store.count_by_source(source.id) == 0


def test_cleanup_removes_chunks_and_progress() -> None:
    notebook_service, indexing, chunk_store, registry = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    source = notebook_service.add_source(
        notebook.id, kind="md", title="a.md", content="# t\n\n본문"
    )
    indexing.register(source)
    indexing.index_source(notebook.id, source.id)
    assert chunk_store.count_by_source(source.id) > 0

    indexing.cleanup_source(source.id)

    assert chunk_store.count_by_source(source.id) == 0
    assert registry.get(source.id) is None
