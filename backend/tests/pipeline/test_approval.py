from app.pipeline.api.schemas import AgentProposal
from app.pipeline.domain.constants import (
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_PENDING,
    PROPOSAL_TYPE_RELATED_CODE_SUGGESTION,
)
from app.pipeline.domain.approval import ApprovalService


def test_approve_returns_approved_copies_without_mutating_originals() -> None:
    service = ApprovalService()
    proposal = AgentProposal(
        id="proposal:1",
        type=PROPOSAL_TYPE_RELATED_CODE_SUGGESTION,
        status=PROPOSAL_STATUS_PENDING,
        target_path="app.py",
        evidence=[],
        confidence=0.4,
        proposed_change="Link context",
    )

    approved = service.approve([proposal])

    assert proposal.status == PROPOSAL_STATUS_PENDING
    assert approved[0].status == PROPOSAL_STATUS_APPROVED
    assert approved[0].id == proposal.id
