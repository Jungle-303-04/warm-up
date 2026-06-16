"""채팅 서비스 테스트(임베딩 검색 기반).

인덱싱(IndexingService)으로 청크를 ChunkStore에 적재한 뒤, 질문 임베딩으로
검색해 citation을 포함한 답변이 나오는지 검증한다. 외부 키 없이 deterministic
임베딩 + in-memory 저장소만 사용한다(네트워크/LLM 호출 없음).
"""

from datetime import UTC, datetime
from itertools import count

from app.notebooks.application.chat_service import ChatService
from app.notebooks.application.indexing_service import IndexingService
from app.notebooks.application.service import NotebookService
from app.notebooks.domain.indexing_progress import IndexProgressRegistry
from app.notebooks.infrastructure.in_memory_chunk_store import InMemoryChunkStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore
from app.repo_rag.infrastructure.embeddings import DeterministicEmbeddingClient

FIXED_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _build():
    counter = count(1)
    store = InMemoryNotebookStore()
    chunk_store = InMemoryChunkStore()
    embedder = DeterministicEmbeddingClient(dimension=64)
    registry = IndexProgressRegistry()
    notebook_service = NotebookService(
        store=store,
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"src-{next(counter)}",
    )
    indexing = IndexingService(
        store=store,
        chunk_store=chunk_store,
        embedder=embedder,
        registry=registry,
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"chunk-{next(counter)}",
    )
    chat = ChatService(store=store, chunk_store=chunk_store, embedder=embedder)
    return notebook_service, indexing, chat


def test_chat_searches_indexed_chunks_and_returns_citation() -> None:
    notebook_service, indexing, chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    auth = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="# 인증\n\nFastAPI 세션 토큰은 쿠키로 저장되고 만료 시간을 검증한다.",
    )
    notebook_service.add_source(
        notebook.id,
        kind="text",
        title="ui.txt",
        content="프론트엔드 색상 팔레트와 카드 레이아웃을 설명한다.",
    )
    # 두 소스 모두 인덱싱.
    for source in notebook_service.list_sources(notebook.id):
        indexing.index_source(notebook.id, source.id)

    result = chat.ask(
        notebook.id,
        question="세션 토큰 만료 검증",
        source_ids=[auth.id],
    )

    assert result.citations
    assert result.citations[0].source_id == auth.id
    assert result.citations[0].source_title == "auth.md"
    # file_path는 md 소스라 None, snippet에 근거 텍스트가 담긴다.
    assert "세션 토큰" in result.citations[0].snippet

    messages = chat.list_messages(notebook.id)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].source_ids == [auth.id]
    assert messages[1].content == result.answer
    assert messages[1].citations[0]["source_id"] == auth.id


def test_chat_repo_citation_includes_file_path() -> None:
    notebook_service, indexing, chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    from app.notebooks.domain.records import SourceRecord

    repo = SourceRecord(
        id="repo-1",
        notebook_id=notebook.id,
        kind="repo",
        title="team/api",
        repository_url="https://github.com/team/api",
        branch="main",
        repo_snapshot=[
            {
                "path": "app/auth/session.py",
                "content": "def validate_session_token(token):\n    return token.ttl > 0\n",
            },
            {"path": "README.md", "content": "# project\n\noverview"},
            {"path": "assets/logo.png", "content": "binary-not-supported"},
        ],
        created_at=FIXED_NOW,
    )
    notebook_service.store.add_source(repo)
    indexing.index_source(notebook.id, repo.id)

    result = chat.ask(notebook.id, question="validate_session_token")

    assert result.citations
    top = result.citations[0]
    assert top.source_id == "repo-1"
    assert top.path == "app/auth/session.py"


def _build_repo_notebook():
    """repo(파일 경로 있는 청크) + md(파일 경로 없는 본문) 소스를 인덱싱한 노트북."""
    notebook_service, indexing, chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    from app.notebooks.domain.records import SourceRecord

    repo = SourceRecord(
        id="repo-1",
        notebook_id=notebook.id,
        kind="repo",
        title="team/api",
        repository_url="https://github.com/team/api",
        branch="main",
        repo_snapshot=[
            {
                "path": "app/auth/session.py",
                "content": "def validate_session_token(token):\n    return token.ttl > 0\n",
            },
            {
                "path": "app/billing/invoice.py",
                "content": "def generate_invoice(order):\n    return order.total\n",
            },
        ],
        created_at=FIXED_NOW,
    )
    notebook_service.store.add_source(repo)
    md = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="notes.md",
        content="# 메모\n\nvalidate_session_token 함수는 세션 토큰의 만료를 검증한다.",
    )
    for source in notebook_service.list_sources(notebook.id):
        indexing.index_source(notebook.id, source.id)
    return chat, notebook, repo, md


def test_chat_file_paths_filters_repo_chunks_but_keeps_non_repo() -> None:
    chat, notebook, _repo, md = _build_repo_notebook()

    # session.py만 범위에 포함. invoice.py(repo)는 제외되어야 하고,
    # file_path가 None인 md 본문 청크는 항상 통과해야 한다.
    result = chat.ask(
        notebook.id,
        question="validate_session_token",
        file_paths=["app/auth/session.py"],
    )

    assert result.citations
    paths = {c.path for c in result.citations}
    # 제외된 repo 파일은 인용에 없어야 한다.
    assert "app/billing/invoice.py" not in paths
    # 비repo(md) 본문 청크(path=None)는 통과한다.
    assert None in paths or "app/auth/session.py" in paths


def test_chat_file_paths_excludes_unselected_repo_file() -> None:
    chat, notebook, _repo, _md = _build_repo_notebook()

    # billing 파일만 선택하면 session.py 청크는 후보에서 빠진다.
    result = chat.ask(
        notebook.id,
        question="generate_invoice 주문 합계",
        file_paths=["app/billing/invoice.py"],
    )

    assert result.citations
    paths = {c.path for c in result.citations}
    assert "app/auth/session.py" not in paths


def test_chat_file_paths_none_searches_all_files() -> None:
    chat, notebook, _repo, _md = _build_repo_notebook()

    # file_paths=None이면 모든 repo 파일이 후보(기존 동작).
    result = chat.ask(notebook.id, question="generate_invoice 주문 합계", file_paths=None)

    assert result.citations
    assert result.citations[0].path == "app/billing/invoice.py"


def test_chat_no_sources_returns_grounding_gap_not_error() -> None:
    notebook_service, _indexing, chat = _build()
    notebook = notebook_service.create_notebook(title="empty")

    result = chat.ask(notebook.id, question="무엇을 담고 있나요?")

    assert result.citations == []
    assert "소스" in result.answer
    messages = chat.list_messages(notebook.id)
    assert [message.role for message in messages] == ["user", "assistant"]


def test_chat_no_matching_chunk_returns_grounding_gap() -> None:
    notebook_service, indexing, chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    source = notebook_service.add_source(
        notebook.id,
        kind="text",
        title="ui.txt",
        content="패널 너비",  # 토큰이 거의 없어 검색에 안 걸리는 짧은 텍스트
    )
    indexing.index_source(notebook.id, source.id)

    # 질문 토큰과 전혀 겹치지 않고 임베딩 점수도 0에 가까운 질의.
    result = chat.ask(
        notebook.id,
        question="zzqq",
        source_ids=[source.id],
    )

    # 근거를 못 찾아도 에러가 아니라 안내 응답.
    assert isinstance(result.answer, str) and result.answer
