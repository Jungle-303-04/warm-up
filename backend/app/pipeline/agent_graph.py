"""LangGraph 기반 제안 생성 어댑터.

그래프 상태, 노드, 조건부 라우팅, MCP tool 실행을 한곳에 모아 둔다.
`app.pipeline.proposer`는 하위 호환 import를 위한 facade만 담당한다.
"""

from __future__ import annotations

import asyncio
import logging
import queue
import threading
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.mcp.client import MCPClient
from app.pipeline.proposal_contracts import ProposalDraft
from app.pipeline.router import CodeReference, RetrievalChunk

_LOGGER = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "당신은 코드 참조와 검색된 근거 청크를 분석해 개선 제안을 만드는 AI 개발자입니다.\n"
    "목표는 수정 대상 파일 경로를 제시하고, 필요한 변경 내용을 설명하며, "
    "근거를 인용하고, 제안의 신뢰도를 평가하는 것입니다.\n\n"
    "제안은 반드시 현재 근거와 직접 관련 있어야 합니다. 논리적 공백이나 실제 문제를 "
    "해결하지 않는 사소한 리팩터링은 제안하지 마세요.\n\n"
    "최종 응답은 반드시 아래 출력 지시를 따르고, 지정된 JSON 형식으로만 작성하세요.\n"
    "출력 지시:\n"
    "{format_instructions}\n"
)

HUMAN_PROMPT = """아래 컨텍스트를 분석하세요.
코드 참조:
{references}

검색 청크:
{chunks}

개선 제안 목록을 생성하세요.
"""


class _LlmProposalItem(BaseModel):
    target_path: str = Field(description="수정 대상 파일 경로")
    proposed_change: str = Field(description="제안하는 코드 변경 내용 설명")
    evidence: list[str] = Field(
        default_factory=list,
        description="이 변경을 뒷받침하는 청크 또는 코드 참조 인용",
    )
    confidence: float = Field(description="0.0 이상 1.0 이하의 신뢰도 점수")


class _LlmProposalList(BaseModel):
    proposals: list[_LlmProposalItem]


class _GraphState(TypedDict):
    references: list[CodeReference]
    chunks: list[RetrievalChunk]
    evidence: dict[str, list[str]]
    drafts: list[ProposalDraft]
    messages: list[Any]
    step_count: int


def _format_references(references: list[CodeReference]) -> str:
    return "\n".join(
        f"- {ref.path}:{ref.symbol} (종류: {ref.kind}, 줄: {ref.line})"
        for ref in references
    )


def _format_chunks(chunks: list[RetrievalChunk]) -> str:
    return "\n".join(
        f"- {chunk.source_path}: {chunk.text} (인용: {chunk.citation})"
        for chunk in chunks
    )


def _run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    """동기 환경(pytest, FastAPI sync)에서 비동기 코루틴을 안전하게 실행한다."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        q: queue.Queue = queue.Queue()

        def target() -> None:
            try:
                sub_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(sub_loop)
                res = sub_loop.run_until_complete(coro)
                q.put((True, res))
            except Exception as exc:
                q.put((False, exc))

        t = threading.Thread(target=target)
        t.start()
        t.join()

        success, val = q.get()
        if success:
            return val
        raise val

    return asyncio.run(coro)


@dataclass
class LangGraphProposer:
    """LangGraph 기반 RAG 분석 제안 엔진.

    MCP 도구를 지원하며 max_steps 한도 내에서 LLM 자율 에이전트가 동작한다.
    """

    chat_model: BaseChatModel
    max_references: int = 5
    max_steps: int = 5
    mcp_client: MCPClient = field(default_factory=MCPClient)

    def __post_init__(self) -> None:
        self._parser = PydanticOutputParser(pydantic_object=_LlmProposalList)
        self._graph = self._build_graph()

    def generate(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[ProposalDraft]:
        if not references:
            return []

        result = _run_async(
            self._graph.ainvoke(
                {
                    "references": references[: self.max_references],
                    "chunks": chunks,
                    "evidence": {},
                    "drafts": [],
                    "messages": [],
                    "step_count": 0,
                }
            )
        )
        return result["drafts"]

    def _build_graph(self):
        builder = StateGraph(_GraphState)

        builder.add_node("gather_evidence", self._gather_evidence)
        builder.add_node("agent", self._agent)
        builder.add_node("execute_tools", self._execute_tools)
        builder.add_node("draft", self._draft)

        builder.add_edge(START, "gather_evidence")
        builder.add_edge("gather_evidence", "agent")
        builder.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "execute_tools": "execute_tools",
                "draft": "draft",
            },
        )
        builder.add_edge("execute_tools", "agent")
        builder.add_edge("draft", END)

        return builder.compile()

    async def _gather_evidence(self, state: _GraphState) -> dict:
        evidence: dict[str, list[str]] = {}
        for chunk in state["chunks"]:
            evidence.setdefault(chunk.source_path, []).append(chunk.citation)

        format_instructions = self._parser.get_format_instructions()
        sys_msg = SystemMessage(
            content=SYSTEM_PROMPT.format(format_instructions=format_instructions)
        )
        human_msg = HumanMessage(
            content=HUMAN_PROMPT.format(
                references=_format_references(state["references"]),
                chunks=_format_chunks(state["chunks"]),
            )
        )

        return {
            "evidence": evidence,
            "messages": [sys_msg, human_msg],
            "step_count": 0,
        }

    async def _agent(self, state: _GraphState) -> dict:
        mcp_tools = await self.mcp_client.list_tools_as_langchain()

        if mcp_tools and hasattr(self.chat_model, "bind_tools"):
            try:
                model_with_tools = self.chat_model.bind_tools(mcp_tools)
            except NotImplementedError:
                model_with_tools = self.chat_model
        else:
            model_with_tools = self.chat_model

        response = await model_with_tools.ainvoke(state["messages"])

        return {
            "messages": state["messages"] + [response],
            "step_count": state["step_count"] + 1,
        }

    def _should_continue(self, state: _GraphState) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            if state["step_count"] <= self.max_steps:
                return "execute_tools"
            _LOGGER.warning(
                "max_steps 한도에 도달해 에이전트 도구 루프를 종료합니다",
                extra={"max_steps": self.max_steps},
            )

        return "draft"

    async def _execute_tools(self, state: _GraphState) -> dict:
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls

        new_messages = list(state["messages"])

        for tool_call in tool_calls:
            name = tool_call["name"]
            args = tool_call["args"]
            call_id = tool_call["id"]

            try:
                result = await self.mcp_client.call_tool(name, args)
            except Exception as exc:
                _LOGGER.warning(
                    "MCP 도구 실행 실패",
                    extra={"tool_name": name, "error": str(exc)},
                )
                result = f"도구 '{name}' 실행 중 오류: {exc!s}"

            new_messages.append(
                ToolMessage(content=result, name=name, tool_call_id=call_id)
            )

        return {"messages": new_messages}

    async def _draft(self, state: _GraphState) -> dict:
        parsed = None

        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                try:
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)
                    parsed = self._parser.parse(content)
                    break
                except Exception:
                    continue

        if parsed is None:
            final_instruction = (
                "수집된 분석 정보를 토대로 최종 제안 목록(proposals)을 생성해 주세요. "
                "이전 지시는 모두 무시하고, 반드시 지정된 JSON 구조 형식으로만 답하세요."
            )
            messages = [*state["messages"], HumanMessage(content=final_instruction)]
            chain = self.chat_model | self._parser

            try:
                parsed = await chain.ainvoke(messages)
            except Exception as exc:
                _LOGGER.warning("최종 제안 파싱 실패", extra={"error": str(exc)})
                parsed = _LlmProposalList(proposals=[])

        evidence = state["evidence"]
        drafts = [
            ProposalDraft(
                target_path=item.target_path,
                proposed_change=item.proposed_change,
                confidence=item.confidence,
                evidence=item.evidence or evidence.get(item.target_path, []),
            )
            for item in parsed.proposals
        ]

        return {"drafts": drafts}
