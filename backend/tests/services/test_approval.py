from app.schemas.pipeline import AgentProposal
from app.services.approval import ApprovalService


def test_approve_returns_approved_copies_without_mutating_originals() -> None:
    service = ApprovalService()
    proposal = AgentProposal(
        id="proposal:1",
        type="related_code_suggestion",
        status="pending",
        target_path="app.py",
        evidence=[],
        confidence=0.4,
        proposed_change="Link context",
    )

    approved = service.approve([proposal])

    assert proposal.status == "pending"
    assert approved[0].status == "approved"
    assert approved[0].id == proposal.id
