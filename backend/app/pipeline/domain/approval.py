from app.pipeline.api.schemas import AgentProposal
from app.pipeline.domain.constants import PROPOSAL_STATUS_APPROVED


class ApprovalService:
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        return [
            proposal.model_copy(update={"status": PROPOSAL_STATUS_APPROVED})
            for proposal in proposals
        ]
