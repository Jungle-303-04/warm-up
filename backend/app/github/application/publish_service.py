"""승인된 제안을 GitHub 코멘트로 발행하는 유스케이스.

도메인 포맷터(format_proposal_comment)로 본문을 만들고 GitHubCommentClient 포트로
작성한다. 어떤 이슈/PR에 달지는 호출자가 issue_number로 지정한다.
"""

from dataclasses import dataclass

from app.github.domain.comment import format_proposal_comment
from app.github.domain.ports import GitHubCommentClient
from app.proposals.domain.records import ProposalRecord


@dataclass(slots=True)
class ProposalPublishService:
    client: GitHubCommentClient

    def publish(self, record: ProposalRecord, issue_number: int) -> str:
        body = format_proposal_comment(record)
        return self.client.create_issue_comment(record.repository, issue_number, body)
