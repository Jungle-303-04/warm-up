import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.github.application.webhook_service import GitHubWebhookService
from app.github.dependencies import get_webhook_service
from app.main import app
from app.repo_rag.api.schemas import RepoRagSyncRequest

SECRET = "testsecret"
_PUSH_BODY = json.dumps(
    {
        "ref": "refs/heads/main",
        "after": "abc123",
        "repository": {"full_name": "o/r", "clone_url": "https://github.com/o/r.git"},
    }
).encode("utf-8")


class _FakeTrigger:
    def __init__(self) -> None:
        self.requests: list[RepoRagSyncRequest] = []

    def trigger(self, request: RepoRagSyncRequest) -> None:
        self.requests.append(request)


@pytest.fixture
def trigger() -> _FakeTrigger:
    return _FakeTrigger()


@pytest.fixture
def client(trigger: _FakeTrigger):
    app.dependency_overrides[get_settings] = lambda: Settings(github_webhook_secret=SECRET)
    app.dependency_overrides[get_webhook_service] = lambda: GitHubWebhookService(
        sync_trigger=trigger
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def _post(client: TestClient, body: bytes, *, event: str = "push", sign: bool = True):
    headers = {"X-GitHub-Event": event, "Content-Type": "application/json"}
    if sign:
        headers["X-Hub-Signature-256"] = _sign(body)
    return client.post("/github/webhook", content=body, headers=headers)


def test_valid_push_triggers_sync(client: TestClient, trigger: _FakeTrigger) -> None:
    response = _post(client, _PUSH_BODY)

    assert response.status_code == 200
    assert response.json()["repository"] == "o/r"
    assert len(trigger.requests) == 1
    assert trigger.requests[0].branch == "main"
    assert trigger.requests[0].trigger_type == "webhook"


def test_invalid_signature_is_rejected(client: TestClient, trigger: _FakeTrigger) -> None:
    response = _post(client, _PUSH_BODY, sign=False)

    assert response.status_code == 401
    assert trigger.requests == []


def test_ping_event_returns_pong(client: TestClient) -> None:
    response = _post(client, b"{}", event="ping")

    assert response.status_code == 200
    assert response.json()["status"] == "pong"


def test_non_push_event_ignored(client: TestClient, trigger: _FakeTrigger) -> None:
    response = _post(client, b"{}", event="issues")

    assert response.json()["status"] == "ignored"
    assert trigger.requests == []
