"""LlmProposer 포트의 LangGraph 구현.

그래프(상태머신)로 제안 생성을 단계화한다:
    gather_evidence  → 청크를 파일 경로별 인용 목록으로 모으고 메시지 초기화.
    agent            → MCP 도구를 바인딩하여 LLM 호출(Function Calling).
    execute_tools    → LLM이 요청한 도구들을 실행하고 상태 갱신(예외 처리 포함).
    draft            → 수집된 최종 정보를 토대로 제안 목록 생성.

무한 루프 방지(max_steps 제한) 및 도구 실행 오류 예외 처리가 반영되어 있습니다.
"""

from __future__ import annotations

import asyncio
import queue
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.pipeline.api.schemas import CodeReference, RetrievalChunk
from app.pipeline.domain.proposer import ProposalDraft
from app.mcp.client import MCPClient

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

SYSTEM_PROMPT = (
    "당신은 코드와 문서를 연결하는 에이전트 보조자입니다. 주어진 코드 참조와 검색 청크를 분석하고, "
    "필요한 경우 등록된 도구(MCP)를 활용하여 추가 검색이나 정보를 획득하세요.\n"
    "최종 분석이 끝나면 반드시 정의된 출력 형식에 맞추어 제안 목록을 반환해 주세요.\n{format_instructions}"
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
    messages: list[BaseMessage]
    step_count: int


def _run_async(coro):
    """실행 중인 이벤트 루프 유무와 상관없이 비동기 코루틴을 동기적으로 실행하는 안전한 헬퍼."""
    try:
        asyncio.get_running_loop()
        is_running = True
    except RuntimeError:
        is_running = False
        
    if is_running:
        q = queue.Queue()
        
        def worker():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                res = new_loop.run_until_complete(coro)
                q.put((True, res))
            except Exception as e:
                q.put((False, e))
            finally:
                new_loop.close()
                
        t = threading.Thread(target=worker)
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
    """주입된 chat_model로 제안 초안을 생성하는 LangGraph 어댑터."""

    chat_model: BaseChatModel
    max_references: int = 5
    max_steps: int = 5

    def __post_init__(self) -> None:
        self.mcp_client = MCPClient()
        self._parser = PydanticOutputParser(pydantic_object=_LlmProposalList)
        self._graph = self._build_graph()

    def generate(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[ProposalDraft]:
        if not references:
            return []

        # 동기 인터페이스 유지를 위해 비동기 그래프 실행기 호출
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
        
        # 조건부 엣지 (루프 또는 완료 분기)
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
            
        # 메시지 초기화
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
        # MCP 서버에서 도구 목록을 조회하여 바인딩
        mcp_tools = await self.mcp_client.list_tools_as_langchain()
        
        if mcp_tools and hasattr(self.chat_model, "bind_tools"):
            try:
                model_with_tools = self.chat_model.bind_tools(mcp_tools)
            except NotImplementedError:
                # GenericFakeChatModel 등 bind_tools 미지원 모델 대비 예외 처리
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
        
        # LLM이 도구 사용을 요청했고, 최대 단계 제한 내인 경우 도구 실행 노드로 진행
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
                # MCP Client를 통해 도구 호출 실행
                result = await self.mcp_client.call_tool(name, args)
            except Exception as e:
                # 에러 발생 시 에이전트 컨텍스트가 무너지지 않도록 텍스트 형태로 우아하게 처리
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
        
        # 최적화: 마지막 AI 응답을 먼저 파싱해보아 추가 LLM 호출 횟수를 1회 줄입니다.
        # 또한 이로써 단 1개의 메시지만 응답하는 테스트 페이크 모델 환경에서도 안정적으로 테스트가 통과합니다.
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                try:
                    parsed = self._parser.parse(msg.content)
                    break
                except Exception:
                    continue
                    
        # 파싱에 실패한 경우에만 최종 취합을 위해 LLM 호출 진행
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
