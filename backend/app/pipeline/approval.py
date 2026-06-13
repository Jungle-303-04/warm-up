from app.pipeline.schemas import AgentProposal


class ApprovalService:
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        return [proposal.model_copy(update={"status": "approved"}) for proposal in proposals]
