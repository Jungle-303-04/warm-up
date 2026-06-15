"""에이전트 제안 생성 포트.

도메인은 "제안 초안을 만든다"는 추상(LlmProposer)만 소유하고,
LangChain/LangGraph 같은 구체 기술은 infrastructure 어댑터가 구현한다(DIP).
이렇게 두면 application/도메인이 LLM 프레임워크를 import 하지 않는다.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.pipeline.api.schemas import CodeReference, ProposalType, RetrievalChunk


@dataclass(frozen=True, slots=True)
class ProposalDraft:
    """LLM이 생성한 제안 초안(상태/식별자 없는 순수 값)."""

    target_path: str
    proposed_change: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    type: ProposalType = ProposalType.RELATED_CODE


@runtime_checkable
class LlmProposer(Protocol):
    """코드 참조와 검색 청크로 제안 초안을 생성하는 포트."""

    def generate(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[ProposalDraft]: ...
