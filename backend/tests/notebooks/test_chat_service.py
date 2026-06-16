from datetime import UTC, datetime
from itertools import count

from app.notebooks.application.chat_service import ChatService
from app.notebooks.application.service import NotebookService
from app.notebooks.domain.records import SourceRecord
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore

FIXED_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _services() -> tuple[NotebookService, ChatService]:
    counter = count(1)
    store = InMemoryNotebookStore()
    notebook = NotebookService(
        store=store,
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"id-{next(counter)}",
    )
    return notebook, ChatService(store=store)


def test_chat_uses_keyword_fallback_and_selected_sources() -> None:
    notebook_service, chat = _services()
    notebook = notebook_service.create_notebook(title="RepoLM")
    auth = notebook_service.add_source(
        notebook.id,
        kind="md",
        title="auth.md",
        content="FastAPI 인증 흐름은 세션 토큰을 쿠키로 저장하고 만료 시간을 검증한다.",
    )
    notebook_service.add_source(
        notebook.id,
        kind="text",
        title="unrelated.txt",
        content="프론트엔드 색상 팔레트와 카드 레이아웃을 설명한다.",
    )

    result = chat.ask(
        notebook.id,
        question="인증 토큰은 어디에서 검증하나요?",
        source_ids=[auth.id],
    )

    assert "선택된 소스" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].source_id == auth.id
    assert "세션 토큰" in result.citations[0].snippet

    messages = chat.list_messages(notebook.id)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content == "인증 토큰은 어디에서 검증하나요?"
    assert messages[0].source_ids == [auth.id]
    assert messages[1].content == result.answer
    assert messages[1].citations[0]["source_id"] == auth.id


def test_chat_reads_repo_snapshot_files() -> None:
    notebook_service, chat = _services()
    notebook = notebook_service.create_notebook(title="RepoLM")
    repo = SourceRecord(
        id="repo-1",
        notebook_id=notebook.id,
        kind="repo",
        title="team/api",
        repository_url="https://github.com/team/api",
        branch="main",
        repo_snapshot=[
            {"path": "app/auth/session.py", "content": "session token ttl validation"},
            {"path": "README.md", "content": "project overview"},
        ],
        created_at=FIXED_NOW,
    )
    notebook_service.store.add_source(repo)

    result = chat.ask(notebook.id, question="session token validation")

    assert result.citations
    assert result.citations[0].source_id == "repo-1"
    assert result.citations[0].path == "app/auth/session.py"


def test_chat_returns_no_error_when_notebook_has_no_sources() -> None:
    notebook_service, chat = _services()
    notebook = notebook_service.create_notebook(title="empty")

    result = chat.ask(notebook.id, question="무엇을 담고 있나요?")

    assert result.citations == []
    assert "소스" in result.answer

    messages = chat.list_messages(notebook.id)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[1].citations == []


def test_chat_returns_grounding_gap_when_no_chunk_matches() -> None:
    notebook_service, chat = _services()
    notebook = notebook_service.create_notebook(title="RepoLM")
    notebook_service.add_source(
        notebook.id,
        kind="text",
        title="ui.txt",
        content="패널 너비와 카드 스타일을 설명한다.",
    )

    result = chat.ask(notebook.id, question="OAuth 콜백은 어떻게 동작하나요?")

    assert result.citations == []
    assert "근거" in result.answer
