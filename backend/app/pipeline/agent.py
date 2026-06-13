from app.pipeline.schemas import AgentProposal, CodeReference, RetrievalChunk


class AgentProposalService:
    def propose(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
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
