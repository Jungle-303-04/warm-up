from app.schemas.pipeline import AgentProposal


class ApprovalService:
    def approve(self, proposals: list[AgentProposal]) -> list[AgentProposal]:
        # Pydantic 객체를 직접 바꾸지 않고 승인 상태가 반영된 copy를 반환한다.
        return [proposal.model_copy(update={"status": "approved"}) for proposal in proposals]
