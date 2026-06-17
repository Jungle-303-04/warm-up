import pytest

from app.pipeline.api.schemas import ProposalStatus
from app.proposals.domain.review import ReviewAction, decide
from app.api.errors import DomainConflictError


def test_approve_pending_becomes_approved() -> None:
    assert decide(ProposalStatus.PENDING, ReviewAction.APPROVE) == ProposalStatus.APPROVED


def test_reject_pending_becomes_rejected() -> None:
    assert decide(ProposalStatus.PENDING, ReviewAction.REJECT) == ProposalStatus.REJECTED


@pytest.mark.parametrize("status", [ProposalStatus.APPROVED, ProposalStatus.REJECTED])
def test_deciding_terminal_proposal_raises(status: ProposalStatus) -> None:
    with pytest.raises(DomainConflictError, match="이미 처리된"):
        decide(status, ReviewAction.APPROVE)
