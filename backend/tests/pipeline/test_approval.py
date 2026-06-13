from app.pipeline.api.schemas import AgentProposal, ProposalStatus, ProposalType
from app.pipeline.domain.approval import ApprovalService


def test_approve_returns_approved_copies_without_mutating_originals() -> None:
    service = ApprovalService()
    proposal = AgentProposal(
        id="proposal:1",
        type=ProposalType.RELATED_CODE,
        status=ProposalStatus.PENDING,
        target_path="app.py",
        evidence=[],
        confidence=0.4,
        proposed_change="Link context",
    )

    approved = service.approve([proposal])

    assert proposal.status == ProposalStatus.PENDING
    assert approved[0].status == ProposalStatus.APPROVED
    assert approved[0].id == proposal.id
