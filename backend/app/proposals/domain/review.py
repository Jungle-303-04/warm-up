"""제안 상태 전이 규칙 (순수 로직, 외부 의존 없음).

게임 퀘스트처럼 제안은 한 번만 결정된다: PENDING에서만 승인/반려로 전이하고,
이미 종료(APPROVED/REJECTED)된 제안은 다시 결정할 수 없다.
"""

from enum import StrEnum

from app.pipeline.api.schemas import ProposalStatus

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
        raise ValueError(f"이미 처리된 제안({current})은 다시 결정할 수 없습니다")
    return _ACTION_RESULT[action]
