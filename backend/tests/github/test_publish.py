from datetime import UTC, datetime

from app.github.application.publish_service import ProposalPublishService
from app.github.domain.comment import format_proposal_comment
from app.pipeline.api.schemas import ProposalStatus, ProposalType
from app.proposals.domain.records import ProposalRecord


def _record() -> ProposalRecord:
    return ProposalRecord(
        id="proposal:app.py:0",
        repository="o/r",
        target_path="app.py",
        type=ProposalType.RELATED_CODE,
        proposed_change="문서에 login 흐름을 추가하세요.",
        evidence=["repo:app.py@abc123"],
        confidence=0.82,
        status=ProposalStatus.APPROVED,
        created_at=datetime(2026, 6, 15, tzinfo=UTC),
    )


class _FakeCommentClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str]] = []

    def create_issue_comment(self, repository: str, issue_number: int, body: str) -> str:
        self.calls.append((repository, issue_number, body))
        return "https://github.com/o/r/issues/7#comment-1"


def test_format_proposal_comment_includes_key_fields() -> None:
    body = format_proposal_comment(_record())

    assert "app.py" in body
    assert "82%" in body
    assert "repo:app.py@abc123" in body
    assert "문서에 login 흐름" in body


def test_publish_posts_formatted_comment() -> None:
    client = _FakeCommentClient()
    service = ProposalPublishService(client=client)

    url = service.publish(_record(), issue_number=7)

    assert url.endswith("#comment-1")
    assert len(client.calls) == 1
    repository, issue_number, body = client.calls[0]
    assert repository == "o/r"
    assert issue_number == 7
    assert "RepoPilot 제안" in body
