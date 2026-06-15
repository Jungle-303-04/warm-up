import pytest

from app.auth.application.service import AuthService
from app.auth.domain.records import GitHubUser
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.auth.infrastructure.session_tokens import SessionTokenCodec


class _FakeOAuthClient:
    def __init__(self) -> None:
        self.exchanged: list[str] = []

    def exchange_code(self, code: str) -> str:
        self.exchanged.append(code)
        return f"gho_token_for_{code}"

    def fetch_user(self, access_token: str) -> GitHubUser:
        return GitHubUser(id=7, login="octocat", name="The Octocat")


def _service(oauth=None, store=None) -> AuthService:
    return AuthService(
        oauth_client=oauth or _FakeOAuthClient(),
        token_store=store or InMemoryGitHubTokenStore(),
        session_codec=SessionTokenCodec(secret="s", ttl_seconds=3600),
        client_id="cid",
        redirect_uri="http://localhost:8000/auth/github/callback",
        scope="read:user repo",
    )


def test_start_login_returns_url_with_state() -> None:
    url, state = _service().start_login()

    assert state in url
    assert url.startswith("https://github.com/login/oauth/authorize")


def test_complete_login_exchanges_code_and_issues_session() -> None:
    store = InMemoryGitHubTokenStore()
    service = _service(store=store)

    result = service.complete_login("abc", received_state="st", expected_state="st")

    assert result.user.login == "octocat"
    assert service.current_user(result.session_token).user_id == 7
    assert store.get(7) == "gho_token_for_abc"


def test_complete_login_rejects_state_mismatch() -> None:
    service = _service()

    with pytest.raises(ValueError, match="state 검증"):
        service.complete_login("abc", received_state="evil", expected_state="st")
