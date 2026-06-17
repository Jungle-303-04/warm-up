"""제안 상태 전이 규칙 및 영속 레코드 정의."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.api.errors import DomainConflictError
from app.pipeline.router import ProposalStatus, ProposalType

TERMINAL_STATUSES = frozenset({ProposalStatus.APPROVED, ProposalStatus.REJECTED})


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


_ACTION_RESULT = {
    ReviewAction.APPROVE: ProposalStatus.APPROVED,
    ReviewAction.REJECT: ProposalStatus.REJECTED,
}


def decide(current: ProposalStatus, action: ReviewAction) -> ProposalStatus:
    if current != ProposalStatus.PENDING:
        raise DomainConflictError(f"이미 처리된 제안({current})은 다시 결정할 수 없습니다")
    return _ACTION_RESULT[action]


@dataclass(slots=True)
class ProposalRecord:
    id: str
    repository: str
    target_path: str
    type: ProposalType
    proposed_change: str
    evidence: list[str]
    confidence: float
    status: ProposalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_reason: str | None = None
