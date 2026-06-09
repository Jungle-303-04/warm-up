from app.schemas.pipeline import AgentProposal, CodeReference, RetrievalChunk


class AgentProposalService:
    def propose(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
        # 실제 LLM 호출 전 단계라 현재는 첫 code reference를 기반으로 proposal 하나만 만든다.
        if not references:
            return []

        reference = references[0]
        evidence = [chunk.citation for chunk in chunks if chunk.source_path == reference.path]

        return [
            AgentProposal(
                id=f"proposal:{reference.id}",
                type="related_code_suggestion",
                status="pending",
                target_path=reference.path,
                evidence=evidence,
                confidence=0.7 if evidence else 0.4,
                proposed_change=f"Link document context to {reference.path}:{reference.symbol}",
            )
        ]
