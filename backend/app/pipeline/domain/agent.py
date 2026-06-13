from app.pipeline.api.schemas import (
    AgentProposal,
    CodeReference,
    ProposalStatus,
    ProposalType,
    RetrievalChunk,
)


class AgentProposalService:
    WITH_EVIDENCE = 0.7
    WITHOUT_EVIDENCE = 0.4
    CHANGE_TEMPLATE = "문서 컨텍스트를 {path}:{symbol} 코드와 연결하세요."

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
                type=ProposalType.RELATED_CODE,
                status=ProposalStatus.PENDING,
                target_path=reference.path,
                evidence=evidence,
                confidence=self._confidence(evidence),
                proposed_change=self.CHANGE_TEMPLATE.format(
                    path=reference.path,
                    symbol=reference.symbol,
                ),
            )
        ]

    def _confidence(self, evidence: list[str]) -> float:
        if evidence:
            return self.WITH_EVIDENCE
        return self.WITHOUT_EVIDENCE
