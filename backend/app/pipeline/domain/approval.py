from app.pipeline.api.schemas import AgentProposal
from app.pipeline.domain.constants import ProposalStatus


class ApprovalService:
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        return [
            proposal.model_copy(update={"status": ProposalStatus.APPROVED})
            for proposal in proposals
        ]
