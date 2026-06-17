"""제안 생성 포트와 DTO.

도메인/서비스 계층은 이 파일의 값 객체와 Protocol에만 의존하고,
LangGraph/LangChain 같은 실행 프레임워크는 infrastructure 성격의 구현 모듈에 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.pipeline.router import CodeReference, ProposalType, RetrievalChunk


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
