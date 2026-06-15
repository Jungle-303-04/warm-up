"""LlmProposer 포트의 LangGraph 구현.

그래프(상태머신)로 제안 생성을 단계화한다:
    gather_evidence  → 청크를 파일 경로별 인용 목록으로 모은다(순수).
    draft            → LCEL 체인(prompt | chat_model | PydanticOutputParser)으로 초안 생성.

분기/반복/사람개입(HITL)이 필요해지면 이 그래프에 노드를 추가하는 방식으로 확장한다.
도메인은 이 모듈을 모르고, 오직 LlmProposer 포트로만 의존한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.pipeline.api.schemas import CodeReference, RetrievalChunk
from app.pipeline.domain.proposer import ProposalDraft

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

SYSTEM_PROMPT = (
    "당신은 코드와 문서를 연결하는 보조자입니다. 주어진 코드 참조와 검색 청크를 보고, "
    "문서를 업데이트하거나 관련 코드를 연결하는 제안을 만드세요. 각 제안은 실제 파일 경로를 "
    "target_path로 지정하고, 0~1 사이 confidence를 부여합니다.\n{format_instructions}"
)
HUMAN_PROMPT = "코드 참조:\n{references}\n\n검색 청크:\n{chunks}"


class _LlmProposal(BaseModel):
    target_path: str = Field(description="제안이 적용될 저장소 기준 파일 경로")
    proposed_change: str = Field(description="제안하는 변경 내용(한국어 한두 문장)")
    confidence: float = Field(description="0~1 사이 신뢰도")


class _LlmProposalList(BaseModel):
    proposals: list[_LlmProposal] = Field(default_factory=list)


class _GraphState(TypedDict):
    references: list[CodeReference]
    chunks: list[RetrievalChunk]
    evidence: dict[str, list[str]]
    drafts: list[ProposalDraft]


@dataclass
class LangGraphProposer:
    """주입된 chat_model로 제안 초안을 생성하는 LangGraph 어댑터."""

    chat_model: BaseChatModel
    max_references: int = 5

    def __post_init__(self) -> None:
        self._parser = PydanticOutputParser(pydantic_object=_LlmProposalList)
        self._prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)]
        ).partial(format_instructions=self._parser.get_format_instructions())
        self._graph = self._build_graph()

    def generate(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[ProposalDraft]:
        if not references:
            return []

        result = self._graph.invoke(
            {"references": references, "chunks": chunks, "evidence": {}, "drafts": []}
        )
        return result["drafts"]

    def _build_graph(self):
        builder = StateGraph(_GraphState)
        builder.add_node("gather_evidence", self._gather_evidence)
        builder.add_node("draft", self._draft)
        builder.add_edge(START, "gather_evidence")
        builder.add_edge("gather_evidence", "draft")
        builder.add_edge("draft", END)
        return builder.compile()

    def _gather_evidence(self, state: _GraphState) -> dict:
        evidence: dict[str, list[str]] = {}
        for chunk in state["chunks"]:
            evidence.setdefault(chunk.source_path, []).append(chunk.citation)
        return {"evidence": evidence}

    def _draft(self, state: _GraphState) -> dict:
        references = state["references"][: self.max_references]
        chain = self._prompt | self.chat_model | self._parser
        parsed: _LlmProposalList = chain.invoke(
            {
                "references": _format_references(references),
                "chunks": _format_chunks(state["chunks"]),
            }
        )

        evidence = state["evidence"]
        drafts = [
            ProposalDraft(
                target_path=item.target_path,
                proposed_change=item.proposed_change,
                confidence=item.confidence,
                evidence=evidence.get(item.target_path, []),
            )
            for item in parsed.proposals
        ]
        return {"drafts": drafts}


def _format_references(references: list[CodeReference]) -> str:
    if not references:
        return "(없음)"
    lines = [f"- {ref.path}:{ref.symbol} ({ref.kind}, line {ref.line})" for ref in references]
    return "\n".join(lines)


def _format_chunks(chunks: list[RetrievalChunk]) -> str:
    if not chunks:
        return "(없음)"
    return "\n".join(f"- [{chunk.citation}] {chunk.text[:200]}" for chunk in chunks)
