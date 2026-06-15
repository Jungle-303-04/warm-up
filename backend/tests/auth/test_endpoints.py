import pytest
from fastapi.testclient import TestClient

from app.auth.application.service import AuthService
from app.auth.dependencies import get_auth_service
from app.auth.domain.records import GitHubUser
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.auth.infrastructure.session_tokens import SessionTokenCodec
from app.main import app

SECRET = "test-secret"


class _FakeOAuthClient:
    def exchange_code(self, code: str) -> str:
        return f"gho_{code}"

    def fetch_user(self, access_token: str) -> GitHubUser:
        return GitHubUser(id=7, login="octocat")


def _service() -> AuthService:
    return AuthService(
        oauth_client=_FakeOAuthClient(),
        token_store=InMemoryGitHubTokenStore(),
        session_codec=SessionTokenCodec(secret=SECRET, ttl_seconds=3600),
        client_id="cid",
        redirect_uri="http://localhost:8000/auth/github/callback",
        scope="read:user repo",
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_auth_service] = _service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_login_redirects_to_github_with_state_cookie(client: TestClient) -> None:
    response = client.get("/auth/github/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith(
        "https://github.com/login/oauth/authorize"
    )
    assert response.cookies.get("rp_oauth_state")


def test_callback_sets_session_cookie_and_redirects(client: TestClient) -> None:
    client.cookies.set("rp_oauth_state", "st")

    response = client.get(
        "/auth/github/callback",
        params={"code": "abc", "state": "st"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.cookies.get("rp_session")


def test_callback_rejects_state_mismatch(client: TestClient) -> None:
    client.cookies.set("rp_oauth_state", "st")

    response = client.get(
        "/auth/github/callback",
        params={"code": "abc", "state": "evil"},
        follow_redirects=False,
    )

    assert response.status_code == 400


def test_me_returns_user_with_valid_session(client: TestClient) -> None:
    token = SessionTokenCodec(secret=SECRET, ttl_seconds=3600).issue(7, "octocat")
    client.cookies.set("rp_session", token)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"user_id": 7, "login": "octocat"}


def test_me_without_session_returns_401(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
