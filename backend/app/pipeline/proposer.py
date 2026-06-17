"""에이전트 제안 생성 포트 및 LangGraph 기반 LLM 분석 구현체."""

import asyncio
import queue
import re
import threading
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar, runtime_checkable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.mcp.client import MCPClient
from app.pipeline.router import CodeReference, ProposalType, RetrievalChunk
from langgraph.graph import END, START, StateGraph

T = TypeVar("T")


# --- 1. LLM 제안 포트 및 DTO 정의 (proposer.py) ---
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


# --- 2. LangGraph 분석 그래프 및 어댑터 정의 (langgraph_proposer.py) ---
SYSTEM_PROMPT = """You are an AI developer analyzing code references and retrieval chunks to propose improvements.
Your goal is to suggest a target file path, explain the proposed change, cite evidence, and rate your confidence.

Ensure your proposals are highly relevant. Do not propose trivial refactorings unless they directly solve a logic gap.

You MUST follow the output instructions and format your final response strictly in the specified JSON format.
Output instructions:
{format_instructions}
"""

HUMAN_PROMPT = """Analyze the following context.
References:
{references}

Chunks:
{chunks}

Generate the list of proposals.
"""


class _LlmProposalItem(BaseModel):
    target_path: str = Field(description="Target file path to modify")
    proposed_change: str = Field(description="Explanation of the proposed code change")
    evidence: list[str] = Field(default_factory=list, description="Citations from chunks/references that support this change")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")


class _LlmProposalList(BaseModel):
    proposals: list[_LlmProposalItem]


class _GraphState(dict):
    references: list[CodeReference]
    chunks: list[RetrievalChunk]
    evidence: dict[str, list[str]]
    drafts: list[ProposalDraft]
    messages: list[Any]
    step_count: int


def _format_references(references: list[CodeReference]) -> str:
    return "\n".join(
        f"- {ref.path}:{ref.symbol} (kind: {ref.kind}, line: {ref.line})"
        for ref in references
    )


def _format_chunks(chunks: list[RetrievalChunk]) -> str:
    return "\n".join(
        f"- {chunk.source_path}: {chunk.text} (citation: {chunk.citation})"
        for chunk in chunks
    )


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """동기 환경(pytest, fastapi sync)에서 비동기 코루틴을 안전하게 실행하기 위한 헬퍼."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 이벤트 루프가 이미 실행 중이면 새로운 스레드에서 서브 루프를 띄워 차단(Deadlock 방지)
        q: queue.Queue = queue.Queue()

        def target():
            try:
                sub_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(sub_loop)
                res = sub_loop.run_until_complete(coro)
                q.put((True, res))
            except Exception as e:
                q.put((False, e))

        t = threading.Thread(target=target)
        t.start()
        t.join()
        
        success, val = q.get()
        if success:
            return val
        else:
            raise val
    else:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


@dataclass
class LangGraphProposer:
    """LangGraph 기반 RAG 분석 제안 엔진.

    MCP 도구를 지원하며, 최대 에이전트 루프 회수(max_steps) 한도 내에서 LLM 자율 에이전트가 동작합니다.
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
                    "references": references,
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
        
        # 노드 정의
        builder.add_node("gather_evidence", self._gather_evidence)
        builder.add_node("agent", self._agent)
        builder.add_node("execute_tools", self._execute_tools)
        builder.add_node("draft", self._draft)
        
        # 엣지 정의
        builder.add_edge(START, "gather_evidence")
        builder.add_edge("gather_evidence", "agent")
        
        # 조건부 엣지
        builder.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "execute_tools": "execute_tools",
                "draft": "draft",
            }
        )
        
        builder.add_edge("execute_tools", "agent")
        builder.add_edge("draft", END)
        
        return builder.compile()

    async def _gather_evidence(self, state: _GraphState) -> dict:
        evidence: dict[str, list[str]] = {}
        for chunk in state["chunks"]:
            evidence.setdefault(chunk.source_path, []).append(chunk.citation)
            
        format_instructions = self._parser.get_format_instructions()
        sys_msg = SystemMessage(content=SYSTEM_PROMPT.format(format_instructions=format_instructions))
        
        refs_str = _format_references(state["references"])
        chunks_str = _format_chunks(state["chunks"])
        user_content = HUMAN_PROMPT.format(references=refs_str, chunks=chunks_str)
        human_msg = HumanMessage(content=user_content)
        
        return {
            "evidence": evidence,
            "messages": [sys_msg, human_msg],
            "step_count": 0
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
            "step_count": state["step_count"] + 1
        }

    def _should_continue(self, state: _GraphState) -> str:
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            if state["step_count"] <= self.max_steps:
                return "execute_tools"
            else:
                print(f"Warning: max_steps limit ({self.max_steps}) reached. Terminating agent loop.")
                
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
            except Exception as e:
                result = f"Error executing tool '{name}': {str(e)}"
                
            new_messages.append(
                ToolMessage(
                    content=result,
                    name=name,
                    tool_call_id=call_id
                )
            )
            
        return {
            "messages": new_messages
        }

    async def _draft(self, state: _GraphState) -> dict:
        parsed = None
        
        # 마지막 AI 응답을 먼저 파싱해보아 추가 LLM 호출 횟수 감소 유도
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                try:
                    parsed = self._parser.parse(msg.content)
                    break
                except Exception:
                    continue
                    
        if parsed is None:
            final_instruction = (
                "수집된 분석 정보를 토대로 최종 제안 목록(proposals)을 생성해 주세요. "
                "이전 지시는 모두 무시하고, 반드시 지정된 JSON 구조 형식으로만 답하세요."
            )
            messages = list(state["messages"]) + [HumanMessage(content=final_instruction)]
            chain = self.chat_model | self._parser
            
            try:
                parsed = await chain.ainvoke(messages)
            except Exception as e:
                print(f"Error parsing final proposals: {e}")
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
