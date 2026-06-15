from dataclasses import dataclass

from app.pipeline.api.schemas import (
    AgentProposal,
    CodeReference,
    ProposalStatus,
    ProposalType,
    RetrievalChunk,
)
from app.pipeline.domain.proposer import LlmProposer, ProposalDraft

WITH_EVIDENCE = 0.7
WITHOUT_EVIDENCE = 0.4
CHANGE_TEMPLATE = "문서 컨텍스트를 {path}:{symbol} 코드와 연결하세요."


@dataclass(slots=True)
class AgentProposalService:
    """제안 생성 유스케이스.

    proposer(LLM 포트)가 주입되면 그 초안으로 제안을 만들고,
    없으면 증거 기반 휴리스틱으로 동작한다(오프라인/테스트 기본값).
    """

    proposer: LlmProposer | None = None

    def propose(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
        if not references:
            return []

        if self.proposer is not None:
            drafts = self.proposer.generate(references, chunks)
            return [self._to_proposal(index, draft) for index, draft in enumerate(drafts)]

        return self._heuristic(references, chunks)

    def _to_proposal(self, index: int, draft: ProposalDraft) -> AgentProposal:
        return AgentProposal(
            id=f"proposal:{draft.target_path}:{index}",
            type=draft.type,
            status=ProposalStatus.PENDING,
            target_path=draft.target_path,
            evidence=draft.evidence,
            confidence=_clamp_confidence(draft.confidence),
            proposed_change=draft.proposed_change,
        )

    def _heuristic(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[AgentProposal]:
        reference = references[0]
        evidence = [chunk.citation for chunk in chunks if chunk.source_path == reference.path]

        return [
            AgentProposal(
                id=f"proposal:{reference.id}",
                type=ProposalType.RELATED_CODE,
                status=ProposalStatus.PENDING,
                target_path=reference.path,
                evidence=evidence,
                confidence=WITH_EVIDENCE if evidence else WITHOUT_EVIDENCE,
                proposed_change=CHANGE_TEMPLATE.format(
                    path=reference.path,
                    symbol=reference.symbol,
                ),
            )
        ]


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, value))
