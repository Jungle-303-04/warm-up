"""채팅 서비스 테스트(임베딩 검색 기반).

인덱싱(IndexingService)으로 청크를 ChunkStore에 적재한 뒤, 질문 임베딩으로
검색해 citation을 포함한 답변이 나오는지 검증한다. 외부 키 없이 deterministic
임베딩 + in-memory 저장소만 사용한다(네트워크/LLM 호출 없음).
"""

from datetime import UTC, datetime
from itertools import count
from typing import Any


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


def test_chat_uses_injected_answerer_for_answer_body() -> None:
    """answerer가 주입되면 ChatService가 그 답변을 본문으로 쓴다(LLM 호출 없이 검증).

    가짜 answerer는 (question, chunks)를 받아 결정론 문자열을 돌려준다. citation은
    여전히 검색된 chunks에서 만들어진다(answerer가 만들지 않음).
    """
    notebook_service, indexing, _chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    auth = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="# 인증\n\nFastAPI 세션 토큰은 쿠키로 저장되고 만료 시간을 검증한다.",
    )
    for source in notebook_service.list_sources(notebook.id):
        indexing.index_source(notebook.id, source.id)

    captured: dict[str, Any] = {}

    def fake_answerer(question, chunks):
        captured["question"] = question
        captured["chunk_count"] = len(chunks)
        # chunks는 TextChunk라 path/source_title 등에 접근 가능해야 한다.
        captured["first_title"] = chunks[0].source_title
        return "LLM이 생성한 답변 본문"

    chat = ChatService(
        store=notebook_service.store,
        chunk_store=indexing.chunk_store,
        embedder=indexing.embedder,
        answerer=fake_answerer,
    )

    result = chat.ask(notebook.id, question="세션 토큰 만료 검증", source_ids=[auth.id])

    # 답변 본문은 answerer가 만든 문자열.
    assert result.answer == "LLM이 생성한 답변 본문"
    assert captured["question"] == "세션 토큰 만료 검증"
    assert captured["chunk_count"] >= 1
    assert captured["first_title"] == "auth.md"
    # citation은 answerer가 아니라 검색된 chunks에서 생성된다.
    assert result.citations
    assert result.citations[0].source_id == auth.id


def test_chat_falls_back_to_deterministic_when_no_answerer() -> None:
    """answerer가 None이면 결정론 폴백(검색 근거 나열) 답변을 쓴다."""
    notebook_service, indexing, chat = _build()  # 기본 answerer=None
    notebook = notebook_service.create_notebook(title="RepoLM")
    auth = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="# 인증\n\nFastAPI 세션 토큰은 쿠키로 저장되고 만료 시간을 검증한다.",
    )
    for source in notebook_service.list_sources(notebook.id):
        indexing.index_source(notebook.id, source.id)

    result = chat.ask(notebook.id, question="세션 토큰 만료 검증", source_ids=[auth.id])

    # 결정론 폴백 고정 문구.
    assert "검색된 근거를 기준으로 답변하면" in result.answer
    assert result.citations


def test_chat_falls_back_when_answerer_returns_empty() -> None:
    """answerer가 빈 문자열/예외를 내면 결정론 폴백으로 안전 전환한다(LLM 호출 없이)."""
    notebook_service, indexing, _chat = _build()
    notebook = notebook_service.create_notebook(title="RepoLM")
    auth = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="# 인증\n\nFastAPI 세션 토큰은 만료 시간을 검증한다.",
    )
    for source in notebook_service.list_sources(notebook.id):
        indexing.index_source(notebook.id, source.id)

    def empty_answerer(question, chunks):
        return "   "  # 공백만 → 폴백되어야 한다.

    chat = ChatService(
        store=notebook_service.store,
        chunk_store=indexing.chunk_store,
        embedder=indexing.embedder,
        answerer=empty_answerer,
    )

    result = chat.ask(notebook.id, question="세션 토큰 만료 검증", source_ids=[auth.id])
    assert "검색된 근거를 기준으로 답변하면" in result.answer


def test_chat_openai_answerer_formats_context_without_network() -> None:
    """ChatOpenAIAnswerer가 가짜 chat_model로 [출처 i] 컨텍스트를 구성하는지 검증.

    네트워크/실제 LLM 호출 없이, invoke에 넘어간 메시지만 캡처해 확인한다.
    """
    from app.notebooks.application.chat_service import TextChunk
    from app.notebooks.infrastructure.chat_answerers import ChatOpenAIAnswerer

    class _FakeResponse:
        content = "근거 기반 답변"

    class _FakeModel:
        def __init__(self):
            self.last_messages: list[tuple[str, str]] | None = None

        def invoke(self, messages):
            self.last_messages = messages
            return _FakeResponse()

    model = _FakeModel()
    answerer = ChatOpenAIAnswerer(model)
    chunks = [
        TextChunk(
            source_id="s1",
            source_title="auth.md",
            text="세션 토큰 만료 검증",
            path="app/auth/session.py",
        )
    ]

    answer = answerer("만료 검증은 어디서?", chunks)

    assert answer == "근거 기반 답변"
    # system + human 메시지 구조.
    assert model.last_messages is not None
    roles = [role for role, _ in model.last_messages]
    assert roles == ["system", "human"]
    human_content = model.last_messages[1][1]
    assert "[출처 1] app/auth/session.py" in human_content
    assert "만료 검증은 어디서?" in human_content


def test_chat_openai_answerer_returns_empty_on_failure() -> None:
    """chat_model.invoke가 예외를 던지면 빈 문자열로 흡수한다(상위에서 폴백)."""
    from app.notebooks.infrastructure.chat_answerers import ChatOpenAIAnswerer

    class _BoomModel:
        def invoke(self, messages):
            raise RuntimeError("network down")

    answerer = ChatOpenAIAnswerer(_BoomModel())
    assert answerer("질문", []) == ""


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
