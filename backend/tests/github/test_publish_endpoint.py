from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims, get_github_token_store
from app.auth.domain.records import SessionClaims
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.github.dependencies import get_comment_client
from app.main import app
from app.pipeline.api.schemas import ProposalStatus, ProposalType
from app.proposals.application.service import ProposalReviewService
from app.proposals.dependencies import get_proposal_review_service
from app.proposals.domain.records import ProposalRecord
from app.proposals.infrastructure.in_memory_store import InMemoryProposalStore


class _FakeCommentClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str]] = []

    def create_issue_comment(self, repository: str, issue_number: int, body: str) -> str:
        self.calls.append((repository, issue_number, body))
        return "https://github.com/o/r/issues/7#comment-1"


def _record() -> ProposalRecord:
    return ProposalRecord(
        id="p1",
        repository="o/r",
        target_path="app.py",
        type=ProposalType.RELATED_CODE,
        proposed_change="문서를 연결하세요.",
        evidence=["repo:app.py@abc"],
        confidence=0.8,
        status=ProposalStatus.APPROVED,
        created_at=datetime(2026, 6, 15, tzinfo=UTC),
    )


def _proposals_with_record() -> ProposalReviewService:
    store = InMemoryProposalStore()
    store.add([_record()])
    return ProposalReviewService(store=store)


@pytest.fixture
def fake_client() -> _FakeCommentClient:
    return _FakeCommentClient()


@pytest.fixture
def client(fake_client: _FakeCommentClient):
    app.dependency_overrides[get_comment_client] = lambda: fake_client
    app.dependency_overrides[get_proposal_review_service] = _proposals_with_record
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_publish_posts_comment_with_user_token(
    client: TestClient, fake_client: _FakeCommentClient
) -> None:
    response = client.post("/github/proposals/p1/publish", json={"issue_number": 7})

    assert response.status_code == 200
    assert response.json()["comment_url"].endswith("#comment-1")
    assert fake_client.calls[0][0] == "o/r"
    assert fake_client.calls[0][1] == 7


def test_publish_unknown_proposal_returns_404(client: TestClient) -> None:
    response = client.post("/github/proposals/nope/publish", json={"issue_number": 7})

    assert response.status_code == 404


def test_publish_without_github_token_returns_403() -> None:
    app.dependency_overrides[get_current_claims] = lambda: SessionClaims(user_id=99, login="x")
    app.dependency_overrides[get_github_token_store] = InMemoryGitHubTokenStore
    try:
        response = TestClient(app).post("/github/proposals/p1/publish", json={"issue_number": 7})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
