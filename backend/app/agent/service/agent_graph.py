import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.domain.chat import (
    AgentTurnResult,
    ChatMessage,
    ChatSession,
    ChatTurn,
    InferredRepositoryRef,
)
from app.agent.service.agent_intent import (
    BASIS_MODE_ADD,
    BASIS_MODE_CLEAR,
    BASIS_MODE_REMOVE,
    BASIS_MODE_REPLACE,
    INTENT_CHANGE_BASIS,
    INTENT_CLARIFY,
    INTENT_GENERAL_CHAT,
    INTENT_LIST_BRANCHES,
    INTENT_LIST_FILES,
    INTENT_LIST_REPOSITORIES,
    INTENT_RAG_ANSWER,
    INTENT_SEARCH_REPOSITORY_TARGETS,
    INTENT_SHOW_BASIS,
    AgentIntent,
    BasisMode,
    detect_basis_mode,
    has_path_focus_hint,
    is_general_chat,
    is_basis_change_request,
    is_branch_list_question,
    is_bare_target_selection,
    is_branch_target_selection,
    is_current_basis_question,
    is_file_list_question,
    is_repository_list_question,
    is_repository_target_search_question,
    is_short_remove_request,
    normalize_text,
)
from app.agent.service.agent_tool_registry import (
    TOOL_CHANGE_BASIS,
    TOOL_CLARIFY,
    TOOL_COMPARE_SNAPSHOTS,
    TOOL_GENERAL_CHAT,
    TOOL_LIST_BRANCHES,
    TOOL_LIST_FILES,
    TOOL_LIST_REPOSITORIES,
    TOOL_RESOLVE_RAG_BASIS,
    TOOL_RETRIEVE_RAG,
    TOOL_SEARCH_REPOSITORY_TARGETS,
    TOOL_SHOW_BASIS,
    AgentTool,
    AgentToolRegistry,
)
from app.agent.service.intent_resolver import FALLBACK_REASON_PREFIX
from app.agent.service.ports import (
    IntentResolver,
    PathTargetResolver,
    RepositoryTargetPlanner,
    ToolCallingLlm,
)
from app.agent.service.rag_answer_prompt import (
    build_answer_messages,
    build_comparison_answer_messages,
    build_evidence_fallback_answer,
    build_no_evidence_answer,
    get_message_content,
)
from app.agent.service.repository_context import (
    build_basis_changed_answer,
    build_branch_list_answer,
    build_available_path_prefixes,
    build_clarification_answer,
    build_comparison_evidence_paths_by_run,
    build_current_basis_answer,
    build_file_snapshot_comparison_answer,
    build_snapshot_comparison_items,
    build_file_list_answer,
    build_inferred_repository_ref,
    build_next_basis_refs,
    build_repository_list_answer,
    build_repository_target_search_answer,
    get_latest_unique_runs_by_repository_branch,
    resolve_runs_from_refs,
    resolve_runs_from_recent_list_ordinal,
    resolve_runs_from_text,
    resolve_single_repository_fallback,
)
from app.rag.api.schema import (
    RagAskRepositoryRefDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagAskSourceDTO,
)
from app.rag.service.ports import AnswerUseCase, RagStore


GENERAL_CHAT_SYSTEM_PROMPT = (
    "You are a Korean coding assistant for a code-trust kanban service. "
    "Respond naturally and briefly. Do not invent repository facts. "
    "If the user seems to need repository/code analysis, suggest asking for the repository list "
    "or naming a repository."
)
MAX_COMPARISON_CHUNKS_PER_RUN = 12
MAX_COMPARISON_CHUNKS_PER_PATH = 2
MAX_SQL_EVIDENCE_SOURCES = 5
MIN_QUERY_TOKEN_LENGTH = 2
IMPLEMENTATION_GAP_QUERY_TERMS = {
    "todo",
    "fixme",
    "placeholder",
    "unfinished",
    "unimplemented",
    "missing",
    "priority",
    "prioritize",
    "implement",
    "미구현",
    "구현",
    "빈구현",
    "우선",
    "우선순위",
    "작업",
    "해야",
}
IMPLEMENTATION_GAP_CHUNK_MARKERS = (
    "todo",
    "fixme",
    "notimplemented",
    "notimplementederror",
    "pass",
    "returnnone",
    "placeholder",
    "미구현",
)


class AgentGraphState(TypedDict, total=False):
    # 각 노드가 다음 노드로 넘기는 작업 메모리다.
    db: Session
    session: ChatSession
    messages: list[ChatMessage]
    turn: ChatTurn
    latest_runs: list[Any]
    intent: AgentIntent
    basis_mode: BasisMode
    tool_queue: list[str]
    last_tool_name: str
    planned_tool_name: str
    planned_rag_tool_name: str
    rag_query: str
    target_runs: list[Any]
    final_refs: list[InferredRepositoryRef]
    rag_response: RagAskResponseDTO
    final_answer: str
    repository_basis_changed: bool


class AgentGraph:
    """채팅 turn 하나를 SQL 메타데이터, 기준 변경, RAG 답변 흐름 중 하나로 보낸다."""

    def __init__(
        self,
        rag_answer_service: AnswerUseCase,
        sql_repository: RagStore,
        tool_calling_llm: ToolCallingLlm,
        repository_target_planner: RepositoryTargetPlanner | None = None,
        intent_resolver: IntentResolver | None = None,
        path_target_resolver: PathTargetResolver | None = None,
    ) -> None:
        self.rag_answer_service = rag_answer_service
        self.sql_repository = sql_repository
        self.tool_calling_llm = tool_calling_llm
        self.repository_target_planner = repository_target_planner
        self.intent_resolver = intent_resolver
        self.path_target_resolver = path_target_resolver
        self.tool_registry = self.build_tool_registry()
        self.graph = self.build_graph()

    def run(
        self,
        db: Session,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> AgentTurnResult:
        """사용자 입력을 graph에 태우고 최종 답변과 다음 답변 기준을 반환한다."""

        state = self.graph.invoke(
            {
                "db": db,
                "session": session,
                "messages": messages,
                "turn": turn,
            }
        )
        return AgentTurnResult(
            content=state["final_answer"],
            inferred_repository_refs=state.get("final_refs"),
            repository_basis_changed=state.get("repository_basis_changed", False),
        )

    def build_graph(self):
        graph = StateGraph(AgentGraphState)

        graph.add_node("collect_repository_context", self.collect_repository_context)
        graph.add_node("classify_intent", self.classify_intent)
        graph.add_node("select_agent_tool", self.select_agent_tool)
        graph.add_node("run_agent_tool", self.run_agent_tool)
        graph.add_node("generate_answer", self.generate_answer)

        graph.set_entry_point("collect_repository_context")
        graph.add_edge("collect_repository_context", "classify_intent")
        graph.add_edge("classify_intent", "select_agent_tool")
        graph.add_edge("select_agent_tool", "run_agent_tool")
        graph.add_conditional_edges(
            "run_agent_tool",
            route_after_tool,
            {
                "run_tool": "run_agent_tool",
                "generate_answer": "generate_answer",
                "end": END,
            },
        )
        graph.add_edge("generate_answer", END)

        return graph.compile()

    def build_tool_registry(self) -> AgentToolRegistry:
        """그래프가 실행할 수 있는 도구를 한 곳에서 조립한다."""

        return AgentToolRegistry(
            [
                AgentTool(
                    TOOL_LIST_REPOSITORIES,
                    "SQL에 저장된 분석 레포지토리 목록을 보여준다.",
                    self.list_repositories_tool,
                ),
                AgentTool(
                    TOOL_LIST_BRANCHES,
                    "선택된 레포지토리의 분석된 브랜치 목록을 보여준다.",
                    self.list_branches_tool,
                ),
                AgentTool(
                    TOOL_SEARCH_REPOSITORY_TARGETS,
                    "사용자 표현과 관련된 레포/브랜치 후보를 검색한다.",
                    self.search_repository_targets_tool,
                ),
                AgentTool(
                    TOOL_SHOW_BASIS,
                    "현재 대화의 답변 기준 레포/브랜치를 보여준다.",
                    self.show_basis_tool,
                ),
                AgentTool(
                    TOOL_LIST_FILES,
                    "선택된 run의 SQL 파일 스냅샷에서 파일/폴더 목록을 보여준다.",
                    self.list_files_tool,
                ),
                AgentTool(
                    TOOL_CHANGE_BASIS,
                    "답변 기준 레포/브랜치를 추가, 교체, 제거, 초기화한다.",
                    self.change_basis_tool,
                ),
                AgentTool(
                    TOOL_RESOLVE_RAG_BASIS,
                    "RAG 검색 전에 어떤 분석 run을 쓸지 확정한다.",
                    self.resolve_rag_basis_tool,
                ),
                AgentTool(
                    TOOL_RETRIEVE_RAG,
                    "확정된 분석 run 기준으로 vector RAG 근거를 찾는다.",
                    self.retrieve_rag_tool,
                ),
                AgentTool(
                    TOOL_COMPARE_SNAPSHOTS,
                    "두 개 이상의 SQL 파일 스냅샷 차이를 비교한다.",
                    self.compare_snapshots_tool,
                ),
                AgentTool(
                    TOOL_GENERAL_CHAT,
                    "레포 분석이 아닌 일반 대화에 짧게 답한다.",
                    self.general_chat_tool,
                ),
                AgentTool(
                    TOOL_CLARIFY,
                    "도구 실행에 필요한 레포 기준을 찾지 못했을 때 되묻는다.",
                    self.clarify_tool,
                ),
            ]
        )

    def collect_repository_context(self, state: AgentGraphState) -> AgentGraphState:
        """SQL에 저장된 최신 레포/브랜치별 분석 run만 모아 다음 노드에 넘긴다."""

        return {
            "latest_runs": get_latest_unique_runs_by_repository_branch(
                self.sql_repository.list_runs(state["db"], limit=100)
            )
        }

    def select_agent_tool(self, state: AgentGraphState) -> AgentGraphState:
        """분류된 intent를 실행 가능한 tool 이름으로 바꾼다."""

        return {
            "tool_queue": [
                state.get("planned_tool_name")
                or select_tool_name(state.get("intent", INTENT_CLARIFY))
            ]
        }

    def run_agent_tool(self, state: AgentGraphState) -> AgentGraphState:
        """tool queue에서 하나를 꺼내 실행하고 남은 queue를 다음 노드에 넘긴다."""

        tool_queue = list(state.get("tool_queue", []))
        if not tool_queue:
            return {"tool_queue": []}

        tool_name = tool_queue.pop(0)
        tool_result = self.tool_registry.run(tool_name, state)
        next_tools = list(tool_result.pop("tool_queue", []))
        return {
            **tool_result,
            "last_tool_name": tool_name,
            "tool_queue": [*next_tools, *tool_queue],
        }

    def classify_intent(self, state: AgentGraphState) -> AgentGraphState:
        """LLM으로 먼저 자연어 의도를 분류하고 실패할 때만 코드 helper로 보강한다."""

        user_input = state["turn"].user_input
        latest_runs = state.get("latest_runs", [])
        current_refs = list(state["turn"].repository_refs)
        messages = state.get("messages", [])

        intent_plan = self.resolve_intent_plan_with_llm(user_input, messages)
        if not is_intent_resolver_fallback(intent_plan):
            return self.build_intent_state(
                intent=intent_plan.intent,
                basis_mode=intent_plan.basis_mode or BASIS_MODE_REPLACE,
                planned_tool_name=getattr(intent_plan, "tool_name", None),
                rag_query=getattr(intent_plan, "rag_query", None),
                user_input=user_input,
                latest_runs=latest_runs,
                current_refs=current_refs,
                messages=messages,
            )

        return self.classify_intent_with_code_fallback(
            user_input=user_input,
            latest_runs=latest_runs,
            current_refs=current_refs,
            messages=messages,
        )

    def classify_intent_with_code_fallback(
        self,
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
    ) -> AgentGraphState:
        """LLM intent 분류가 실패했을 때만 기존 키워드 helper로 최소 동작을 보장한다."""

        if is_repository_list_question(user_input):
            return {"intent": INTENT_LIST_REPOSITORIES}

        if is_repository_target_search_question(user_input):
            return {
                "intent": INTENT_SEARCH_REPOSITORY_TARGETS,
                "target_runs": self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    prefer_planner=True,
                    allow_repository_default=False,
                ),
            }

        if is_current_basis_question(user_input):
            return {"intent": INTENT_SHOW_BASIS}

        if is_general_chat(user_input):
            return {"intent": INTENT_GENERAL_CHAT}

        if is_short_follow_up_selection(user_input):
            return {
                "intent": INTENT_CHANGE_BASIS,
                "basis_mode": BASIS_MODE_REPLACE,
                "target_runs": self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            }

        if is_bare_target_selection(user_input):
            basis_mode = detect_bare_target_basis_mode(current_refs)
            return {
                "intent": INTENT_CHANGE_BASIS,
                "basis_mode": basis_mode,
                "target_runs": self.resolve_basis_change_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    basis_mode=basis_mode,
                ),
            }

        if is_branch_target_selection(user_input):
            return {
                "intent": INTENT_CHANGE_BASIS,
                "basis_mode": detect_bare_target_basis_mode(current_refs),
                "target_runs": self.resolve_basis_change_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    basis_mode=detect_bare_target_basis_mode(current_refs),
                ),
            }

        if is_file_list_question(user_input):
            return {
                "intent": INTENT_LIST_FILES,
                "target_runs": self.resolve_runs_for_current_question(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            }

        if is_branch_list_question(user_input):
            return {
                "intent": INTENT_LIST_BRANCHES,
                "target_runs": self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            }

        if is_basis_change_request(user_input):
            basis_mode = detect_basis_mode(user_input)
            return {
                "intent": INTENT_CHANGE_BASIS,
                "basis_mode": basis_mode,
                "target_runs": self.resolve_basis_change_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    basis_mode=basis_mode,
                ),
            }

        return {"intent": INTENT_RAG_ANSWER}

    def build_intent_state(
        self,
        intent: AgentIntent,
        basis_mode: BasisMode,
        planned_tool_name: str | None,
        rag_query: str | None,
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
    ) -> AgentGraphState:
        """분류된 intent를 LangGraph state로 바꾼다."""

        if intent == INTENT_LIST_REPOSITORIES:
            return build_planned_intent_state(
                INTENT_LIST_REPOSITORIES,
                planned_tool_name,
                rag_query,
            )
        if intent == INTENT_LIST_BRANCHES:
            return build_planned_intent_state(
                INTENT_LIST_BRANCHES,
                planned_tool_name,
                rag_query,
                target_runs=self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            )
        if intent == INTENT_SEARCH_REPOSITORY_TARGETS:
            return build_planned_intent_state(
                INTENT_SEARCH_REPOSITORY_TARGETS,
                planned_tool_name,
                rag_query,
                target_runs=self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    prefer_planner=True,
                    allow_repository_default=False,
                ),
            )
        if intent == INTENT_SHOW_BASIS:
            return build_planned_intent_state(INTENT_SHOW_BASIS, planned_tool_name, rag_query)
        if intent == INTENT_GENERAL_CHAT:
            return build_planned_intent_state(INTENT_GENERAL_CHAT, planned_tool_name, rag_query)
        if intent == INTENT_LIST_FILES:
            return build_planned_intent_state(
                INTENT_LIST_FILES,
                planned_tool_name,
                rag_query,
                target_runs=self.resolve_runs_for_current_question(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            )
        if intent == INTENT_CHANGE_BASIS:
            basis_mode = resolve_basis_mode(
                user_input=user_input,
                current_refs=current_refs,
                fallback_mode=basis_mode,
            )
            return build_planned_intent_state(
                INTENT_CHANGE_BASIS,
                planned_tool_name,
                rag_query,
                basis_mode=basis_mode,
                target_runs=self.resolve_basis_change_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                    basis_mode=basis_mode,
                ),
            )

        return build_planned_intent_state(INTENT_RAG_ANSWER, planned_tool_name, rag_query)

    def list_repositories_tool(self, state: AgentGraphState) -> AgentGraphState:
        """SQL run 메타데이터를 레포지토리 단위 목록으로 답한다."""

        return self.build_static_tool_answer(
            state,
            build_repository_list_answer(state.get("latest_runs", [])),
        )

    def list_branches_tool(self, state: AgentGraphState) -> AgentGraphState:
        """SQL run 메타데이터에서 특정 레포지토리의 브랜치 목록을 답한다."""

        final_answer = build_branch_list_answer(
            user_input=state["turn"].user_input,
            latest_runs=state.get("latest_runs", []),
            target_runs=state.get("target_runs", []),
            current_refs=list(state["turn"].repository_refs),
            messages=state.get("messages", []),
        )
        return self.build_static_tool_answer(state, final_answer)

    def search_repository_targets_tool(self, state: AgentGraphState) -> AgentGraphState:
        """사용자 표현에 맞는 레포/브랜치 후보를 SQL run 후보에서 찾아 답한다."""

        final_answer = build_repository_target_search_answer(
            user_input=state["turn"].user_input,
            latest_runs=state.get("latest_runs", []),
            target_runs=state.get("target_runs", []),
        )
        return self.build_static_tool_answer(state, final_answer)

    def show_basis_tool(self, state: AgentGraphState) -> AgentGraphState:
        """현재 대화 turn에 저장된 답변 기준을 보여준다."""

        return self.build_static_tool_answer(
            state,
            build_current_basis_answer(list(state["turn"].repository_refs)),
        )

    def build_static_tool_answer(
        self,
        state: AgentGraphState,
        final_answer: str,
    ) -> AgentGraphState:
        """기준을 바꾸지 않는 SQL 메타데이터 tool 응답 형태를 통일한다."""

        return {
            "final_answer": final_answer,
            "final_refs": list(state["turn"].repository_refs),
            "repository_basis_changed": False,
        }

    def list_files_tool(self, state: AgentGraphState) -> AgentGraphState:
        """폴더/파일 구조 질문은 vector 검색 대신 SQL 파일 스냅샷에서 답한다."""

        target_runs = state.get("target_runs", [])
        file_snapshots_by_run = {
            run.id: self.sql_repository.list_file_snapshots(state["db"], run.id)
            for run in target_runs
        }
        skipped_files_by_run = {
            run.id: self.sql_repository.list_skipped_files(state["db"], run.id)
            for run in target_runs
        }
        available_paths = [
            snapshot.path
            for snapshots in file_snapshots_by_run.values()
            for snapshot in snapshots
            if snapshot.path
        ]
        planned_focus = self.resolve_path_focus_with_planner(
            user_input=state["turn"].user_input,
            available_paths=available_paths,
            messages=state.get("messages", []),
        )
        final_refs = [build_inferred_repository_ref(run) for run in target_runs]
        return {
            "final_answer": build_file_list_answer(
                user_input=state["turn"].user_input,
                target_runs=target_runs,
                file_snapshots_by_run=file_snapshots_by_run,
                skipped_files_by_run=skipped_files_by_run,
                planned_focus=planned_focus,
            ),
            "final_refs": final_refs or list(state["turn"].repository_refs),
            "repository_basis_changed": bool(final_refs),
        }

    def compare_snapshots_tool(self, state: AgentGraphState) -> AgentGraphState:
        """두 개 이상의 선택 기준은 SQL 파일 스냅샷으로 먼저 구조적 차이를 답한다."""

        target_runs = state.get("target_runs", [])
        file_snapshots_by_run = {
            run.id: self.sql_repository.list_file_snapshots(state["db"], run.id)
            for run in target_runs
        }
        final_refs = [build_inferred_repository_ref(run) for run in target_runs]
        snapshot_summary = build_file_snapshot_comparison_answer(
            user_input=state["turn"].user_input,
            target_runs=target_runs,
            file_snapshots_by_run=file_snapshots_by_run,
        )
        if len(target_runs) < 2:
            return {
                "final_answer": snapshot_summary,
                "final_refs": final_refs,
                "repository_basis_changed": bool(final_refs),
            }

        comparison_items = build_snapshot_comparison_items(
            target_runs=target_runs,
            file_snapshots_by_run=file_snapshots_by_run,
        )
        chunks_by_run = self.collect_comparison_chunks(
            db=state["db"],
            target_runs=target_runs,
            evidence_paths_by_run=build_comparison_evidence_paths_by_run(
                user_input=state["turn"].user_input,
                comparison_items=comparison_items,
            ),
        )
        return {
            "final_answer": self.generate_snapshot_comparison_answer(
                question=state["turn"].user_input,
                snapshot_summary=snapshot_summary,
                chunks_by_run=chunks_by_run,
            ),
            "final_refs": final_refs,
            "repository_basis_changed": bool(final_refs),
        }

    def collect_comparison_chunks(
        self,
        db: Session,
        target_runs: list[Any],
        evidence_paths_by_run: dict[int, list[str]],
    ) -> list[tuple[Any, list[Any]]]:
        """스냅샷 차이가 난 대표 파일들의 SQL 청크를 run별로 모은다."""

        chunks_by_run: list[tuple[Any, list[Any]]] = []
        for run in target_runs:
            evidence_paths = set(evidence_paths_by_run.get(run.id, []))
            if not evidence_paths:
                continue

            selected_chunks = select_chunks_for_paths(
                chunks=self.sql_repository.list_chunks(db, run.id),
                evidence_paths=evidence_paths,
            )
            if selected_chunks:
                chunks_by_run.append((run, selected_chunks))
        return chunks_by_run

    def generate_snapshot_comparison_answer(
        self,
        question: str,
        snapshot_summary: str,
        chunks_by_run: list[tuple[Any, list[Any]]],
    ) -> str:
        """파일 스냅샷 비교와 SQL 코드 청크를 LLM에게 넘겨 기능 차이를 설명한다."""

        if not chunks_by_run:
            return snapshot_summary

        try:
            ai_message = self.tool_calling_llm.invoke(
                build_comparison_answer_messages(
                    question=question,
                    snapshot_summary=snapshot_summary,
                    chunks_by_run=chunks_by_run,
                ),
                tools=[],
            )
            final_answer = get_message_content(ai_message)
        except Exception:
            return snapshot_summary

        return final_answer or snapshot_summary

    def change_basis_tool(self, state: AgentGraphState) -> AgentGraphState:
        """사용자가 지정한 레포 이름을 SQL run에 매핑해 다음 답변 기준으로 저장한다."""

        current_refs = list(state["turn"].repository_refs)
        target_runs = state.get("target_runs", [])
        mode = state.get("basis_mode", BASIS_MODE_REPLACE)

        final_refs = build_next_basis_refs(
            current_refs=current_refs,
            target_runs=target_runs,
            mode=mode,
        )

        if mode == BASIS_MODE_REMOVE and not target_runs:
            final_refs = remove_last_basis_ref_if_short_request(
                user_input=state["turn"].user_input,
                current_refs=current_refs,
            )
            if final_refs == current_refs:
                return {
                    "final_answer": (
                        "어떤 답변 기준을 뺄지 찾지 못했습니다. "
                        "예: minjeong 브랜치 빼, woonyong 빼처럼 제거할 브랜치를 적어 주세요."
                    ),
                    "final_refs": current_refs,
                    "repository_basis_changed": False,
                }

        elif mode != BASIS_MODE_CLEAR and not target_runs:
            return {
                "final_answer": (
                    "어떤 레포지토리를 답변 기준으로 바꿀지 찾지 못했습니다. "
                    "예: Jungle-303-04/warm-up, minmings111/github.io처럼 레포 이름을 적어 주세요."
                ),
                "final_refs": current_refs,
                "repository_basis_changed": False,
            }

        return {
            "final_answer": build_basis_changed_answer(final_refs, mode),
            "final_refs": final_refs,
            "repository_basis_changed": True,
        }

    def resolve_rag_basis_tool(self, state: AgentGraphState) -> AgentGraphState:
        """RAG 검색 전에 질문이 어떤 분석 run을 기준으로 삼는지 확정한다."""

        current_refs = list(state["turn"].repository_refs)
        if current_refs:
            target_runs = resolve_runs_from_refs(current_refs, state.get("latest_runs", []))
            if not target_runs:
                return {
                    "target_runs": [],
                    "final_refs": current_refs,
                    "tool_queue": [TOOL_CLARIFY],
                }
            return {
                "target_runs": target_runs,
                "final_refs": current_refs,
                "tool_queue": build_rag_next_tool_queue(state, target_runs),
            }

        target_runs = self.resolve_target_runs(
            user_input=state["turn"].user_input,
            latest_runs=state.get("latest_runs", []),
            current_refs=current_refs,
            messages=state.get("messages", []),
            prefer_planner=is_short_follow_up_selection(state["turn"].user_input),
        )
        if target_runs:
            return {
                "target_runs": target_runs,
                "final_refs": [build_inferred_repository_ref(run) for run in target_runs],
                "repository_basis_changed": True,
                "tool_queue": build_rag_next_tool_queue(state, target_runs),
            }

        single_run = resolve_single_repository_fallback(state.get("latest_runs", []))
        if single_run is not None:
            return {
                "target_runs": [single_run],
                "final_refs": [build_inferred_repository_ref(single_run)],
                "repository_basis_changed": True,
                "tool_queue": [TOOL_RETRIEVE_RAG],
            }

        return {
            "target_runs": [],
            "final_refs": current_refs,
            "tool_queue": [TOOL_CLARIFY],
        }

    def retrieve_rag_tool(self, state: AgentGraphState) -> AgentGraphState:
        """확정된 run 기준을 RAG DTO로 바꿔 vector 검색과 LLM용 근거 조회를 실행한다."""

        refs = [
            RagAskRepositoryRefDTO(
                repository_full_name=run.repository_full_name,
                branch=run.branch,
                commit_sha=run.commit_sha,
            )
            for run in state.get("target_runs", [])
            if run.repository_full_name
        ]
        rag_response = self.rag_answer_service.answer(
            state["db"],
            RagAskRequestDTO(
                question=state.get("rag_query") or state["turn"].user_input,
                repository_refs=refs,
                limit=5,
            ),
        )
        return {
            "rag_response": append_sql_chunk_sources(
                rag_response=rag_response,
                sql_sources=self.collect_sql_sources_for_question(
                    db=state["db"],
                    target_runs=state.get("target_runs", []),
                    question=state.get("rag_query") or state["turn"].user_input,
                ),
            )
        }

    def collect_sql_sources_for_question(
        self,
        db: Session,
        target_runs: list[Any],
        question: str,
    ) -> list[RagAskSourceDTO]:
        """vector 검색이 놓친 코드 근거를 보완하기 위해 SQL 청크도 질문 단어로 찾는다."""

        query_tokens = build_query_tokens(question)
        if not query_tokens:
            return []

        implementation_gap_query = is_implementation_gap_query(query_tokens)
        scored_chunks: list[tuple[int, Any]] = []
        for run in target_runs:
            for chunk in self.sql_repository.list_chunks(db, run.id):
                score = score_chunk_for_query(
                    chunk=chunk,
                    query_tokens=query_tokens,
                    implementation_gap_query=implementation_gap_query,
                )
                if score <= 0:
                    continue
                scored_chunks.append((score, chunk))

        return [
            build_sql_source_from_chunk(chunk)
            for _, chunk in sorted(
                scored_chunks,
                key=lambda item: (-item[0], getattr(item[1], "id", 0)),
            )[:MAX_SQL_EVIDENCE_SOURCES]
        ]

    def resolve_target_runs(
        self,
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
        prefer_planner: bool = False,
        allow_repository_default: bool = True,
    ) -> list[Any]:
        """규칙으로 먼저 찾고, 애매한 표현은 LLM planner가 SQL 후보 안에서만 다시 고른다."""

        ordinal_runs = resolve_runs_from_recent_list_ordinal(
            user_input=user_input,
            latest_runs=latest_runs,
            messages=messages,
        )
        if ordinal_runs:
            return ordinal_runs

        if prefer_planner:
            planner_runs = self.infer_runs_with_planner(user_input, latest_runs, messages)
            if planner_runs:
                return planner_runs

        target_runs = resolve_runs_from_text(
            user_input=user_input,
            latest_runs=latest_runs,
            current_refs=current_refs,
            messages=messages,
            allow_repository_default=allow_repository_default,
        )
        if target_runs:
            return target_runs

        return self.infer_runs_with_planner(user_input, latest_runs, messages)

    def resolve_runs_for_current_question(
        self,
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
    ) -> list[Any]:
        """질문이 특정 브랜치를 말하면 그 대상을 우선하고, 아니면 현재 기준을 쓴다."""

        if has_explicit_target_hint(user_input):
            current_candidate_runs = resolve_runs_from_refs(current_refs, latest_runs)
            if current_candidate_runs:
                target_runs = self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=current_candidate_runs,
                    current_refs=[],
                    messages=messages,
                    prefer_planner=True,
                    allow_repository_default=False,
                )
                if target_runs:
                    return target_runs

            target_runs = self.resolve_target_runs(
                user_input=user_input,
                latest_runs=latest_runs,
                current_refs=[],
                messages=messages,
                prefer_planner=True,
                allow_repository_default=False,
            )
            if target_runs:
                return target_runs

        current_runs = resolve_runs_from_refs(current_refs, latest_runs)
        if current_runs:
            return current_runs

        return self.resolve_target_runs(
            user_input=user_input,
            latest_runs=latest_runs,
            current_refs=current_refs,
            messages=messages,
        )

    def resolve_basis_change_target_runs(
        self,
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
        basis_mode: BasisMode,
    ) -> list[Any]:
        """기준 변경 요청에서 실제로 추가/교체/제거할 SQL run을 찾는다."""

        if basis_mode == BASIS_MODE_CLEAR:
            return []

        if basis_mode != BASIS_MODE_REMOVE:
            return self.resolve_target_runs(
                user_input=user_input,
                latest_runs=latest_runs,
                current_refs=current_refs,
                messages=messages,
                prefer_planner=True,
                allow_repository_default=False,
            )

        if is_short_remove_request(user_input):
            return []

        current_runs = resolve_runs_from_refs(current_refs, latest_runs)
        if not current_runs:
            return []

        target_runs = resolve_runs_from_text(
            user_input=user_input,
            latest_runs=current_runs,
            current_refs=current_refs,
            messages=messages,
            allow_repository_default=False,
        )
        if target_runs:
            return target_runs

        return self.infer_runs_with_planner(
            user_input=build_remove_planner_input(user_input),
            latest_runs=current_runs,
            messages=messages,
        )

    def resolve_intent_plan_with_llm(
        self,
        user_input: str,
        messages: list[ChatMessage],
    ) -> Any:
        """키워드 helper가 놓친 자연어 의도를 LLM resolver로 한 번 더 분류한다."""

        if self.intent_resolver is None:
            return SimpleIntentPlan(intent=INTENT_RAG_ANSWER, basis_mode=None)
        return self.intent_resolver.resolve_intent(user_input, messages)

    def infer_runs_with_planner(
        self,
        user_input: str,
        latest_runs: list[Any],
        messages: list[ChatMessage],
    ) -> list[Any]:
        """LLM resolver 결과를 실제 SQL run 객체 목록으로 되돌린다."""

        if self.repository_target_planner is None:
            return []

        plan = self.repository_target_planner.infer_repository_refs(
            user_input=user_input,
            runs=latest_runs,
            messages=messages,
        )
        if not plan.inferred_repository_refs:
            return []
        return resolve_runs_from_refs(plan.inferred_repository_refs, latest_runs)

    def resolve_path_focus_with_planner(
        self,
        user_input: str,
        available_paths: list[str],
        messages: list[ChatMessage],
    ) -> str | None:
        """오타가 섞인 폴더 표현은 LLM이 실제 SQL path 후보 안에서만 고르게 한다."""

        if (
            self.path_target_resolver is None
            or not available_paths
            or not has_path_focus_hint(user_input)
        ):
            return None

        path_candidates = build_available_path_prefixes(available_paths)
        if not path_candidates:
            return None

        plan = self.path_target_resolver.resolve_path_target(
            user_input=user_input,
            path_candidates=path_candidates,
            messages=messages,
        )
        return plan.selected_path

    def generate_answer(self, state: AgentGraphState) -> AgentGraphState:
        """검색 근거가 있을 때만 LLM을 호출해 최종 자연어 답변을 만든다."""

        rag_response = state["rag_response"]
        if not rag_response.sources:
            return {
                "final_answer": build_no_evidence_answer(state.get("final_refs", [])),
            }

        try:
            ai_message = self.tool_calling_llm.invoke(
                build_answer_messages(
                    question=state["turn"].user_input,
                    rag_response=rag_response,
                ),
                tools=[],
            )
            final_answer = get_message_content(ai_message)
        except Exception:
            final_answer = build_evidence_fallback_answer(rag_response)

        return {
            "final_answer": final_answer,
        }

    def general_chat_tool(self, state: AgentGraphState) -> AgentGraphState:
        """레포 검색이 아닌 짧은 대화는 LLM으로 자연스럽게 응답한다."""

        try:
            ai_message = self.tool_calling_llm.invoke(
                [
                    SystemMessage(content=GENERAL_CHAT_SYSTEM_PROMPT),
                    HumanMessage(content=state["turn"].user_input),
                ],
                tools=[],
            )
            final_answer = get_message_content(ai_message)
        except Exception:
            final_answer = "응. 레포 기준이 필요하면 레포 목록부터 보여줄게."

        return {
            "final_answer": final_answer,
            "final_refs": list(state["turn"].repository_refs),
            "repository_basis_changed": False,
        }

    def clarify_tool(self, state: AgentGraphState) -> AgentGraphState:
        """검색 기준을 확정하지 못했을 때 가능한 레포 예시를 보여준다."""

        return {
            "final_answer": build_clarification_answer(state.get("latest_runs", [])),
            "final_refs": list(state["turn"].repository_refs),
            "repository_basis_changed": False,
        }


def select_tool_name(intent: AgentIntent) -> str:
    """LLM이 분류한 intent를 실제 실행 가능한 agent tool 이름으로 바꾼다."""

    return {
        INTENT_LIST_REPOSITORIES: TOOL_LIST_REPOSITORIES,
        INTENT_LIST_BRANCHES: TOOL_LIST_BRANCHES,
        INTENT_SEARCH_REPOSITORY_TARGETS: TOOL_SEARCH_REPOSITORY_TARGETS,
        INTENT_LIST_FILES: TOOL_LIST_FILES,
        INTENT_SHOW_BASIS: TOOL_SHOW_BASIS,
        INTENT_CHANGE_BASIS: TOOL_CHANGE_BASIS,
        INTENT_RAG_ANSWER: TOOL_RESOLVE_RAG_BASIS,
        INTENT_GENERAL_CHAT: TOOL_GENERAL_CHAT,
        INTENT_CLARIFY: TOOL_CLARIFY,
    }.get(intent, TOOL_CLARIFY)


def select_chunks_for_paths(
    chunks: list[Any],
    evidence_paths: set[str],
) -> list[Any]:
    """대표 변경 파일별로 너무 많은 chunk가 들어가지 않게 LLM 입력을 제한한다."""

    selected_chunks = []
    selected_count_by_path: dict[str, int] = {}
    for chunk in chunks:
        path = getattr(chunk, "path", None)
        if path not in evidence_paths:
            continue
        path_count = selected_count_by_path.get(path, 0)
        if path_count >= MAX_COMPARISON_CHUNKS_PER_PATH:
            continue

        selected_chunks.append(chunk)
        selected_count_by_path[path] = path_count + 1
        if len(selected_chunks) >= MAX_COMPARISON_CHUNKS_PER_RUN:
            break
    return selected_chunks


def append_sql_chunk_sources(
    rag_response: RagAskResponseDTO,
    sql_sources: list[RagAskSourceDTO],
) -> RagAskResponseDTO:
    """vector 근거 뒤에 SQL 청크 근거를 중복 없이 붙인다."""

    if not sql_sources:
        return rag_response

    merged_sources = []
    seen_keys = set()
    for source in [*rag_response.sources, *sql_sources]:
        key = (source.citation, source.path, source.chunk_type)
        if key in seen_keys:
            continue
        merged_sources.append(source)
        seen_keys.add(key)
    return rag_response.model_copy(update={"sources": merged_sources})


def build_query_tokens(question: str) -> list[str]:
    """질문 문장에서 SQL 청크 점수화에 쓸 의미 단어만 추린다."""

    tokens = []
    for token in re.findall(r"[0-9a-zA-Z가-힣_./-]+", normalize_text(question)):
        if len(token) < MIN_QUERY_TOKEN_LENGTH:
            continue
        if token in {"the", "and", "for", "with", "these", "selected", "branches"}:
            continue
        tokens.append(token)
    return dedupe_texts(tokens)


def score_chunk_for_query(
    chunk: Any,
    query_tokens: list[str],
    implementation_gap_query: bool = False,
) -> int:
    """질문 단어가 path, symbol, chunk text에 얼마나 직접 등장하는지 점수화한다."""

    path_text = normalize_text(getattr(chunk, "path", "") or "")
    symbol_text = normalize_text(getattr(chunk, "symbol_name", "") or "")
    body_text = normalize_text(getattr(chunk, "chunk_text", "") or "")
    chunk_type_text = normalize_text(getattr(chunk, "chunk_type", "") or "")

    score = 0
    if implementation_gap_query and has_implementation_gap_signal(
        chunk_type_text,
        body_text,
    ):
        score += 30

    for token in query_tokens:
        if token in path_text:
            score += 4
        if token in symbol_text:
            score += 3
        if token in chunk_type_text:
            score += 2
        if token in body_text:
            score += 1
    return score


def is_implementation_gap_query(query_tokens: list[str]) -> bool:
    """사용자가 TODO, 미구현, 우선 작업처럼 구현 공백을 찾는 질문인지 본다."""

    return any(token in IMPLEMENTATION_GAP_QUERY_TERMS for token in query_tokens)


def has_implementation_gap_signal(chunk_type_text: str, body_text: str) -> bool:
    """청크 자체에 빈 구현이나 TODO 계열 신호가 있는지 확인한다."""

    if "placeholder" in chunk_type_text:
        return True
    compact_body = body_text.replace("_", "").replace(" ", "")
    return any(marker in compact_body for marker in IMPLEMENTATION_GAP_CHUNK_MARKERS)


def build_sql_source_from_chunk(chunk: Any) -> RagAskSourceDTO:
    """SQL chunk record를 RAG 답변 LLM이 읽는 source DTO로 맞춘다."""

    return RagAskSourceDTO(
        citation=getattr(chunk, "citation", "") or getattr(chunk, "path", ""),
        path=getattr(chunk, "path", ""),
        chunk_type=getattr(chunk, "chunk_type", ""),
        content=getattr(chunk, "chunk_text", ""),
    )


def dedupe_texts(values: list[str]) -> list[str]:
    """순서를 유지하면서 중복 단어를 제거한다."""

    deduped = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def build_planned_intent_state(
    intent: AgentIntent,
    planned_tool_name: str | None,
    rag_query: str | None,
    basis_mode: BasisMode | None = None,
    target_runs: list[Any] | None = None,
) -> AgentGraphState:
    """LLM planner가 고른 intent/tool/search query를 graph state에 보존한다."""

    state: AgentGraphState = {
        "intent": intent,
    }
    if basis_mode is not None:
        state["basis_mode"] = basis_mode
    if planned_tool_name:
        normalized_tool = normalize_planned_tool_name(intent, planned_tool_name)
        state["planned_tool_name"] = normalized_tool
        if normalized_tool != planned_tool_name:
            state["planned_rag_tool_name"] = planned_tool_name
    if rag_query:
        state["rag_query"] = rag_query
    if target_runs is not None:
        state["target_runs"] = target_runs
    return state


def normalize_planned_tool_name(intent: AgentIntent, tool_name: str) -> str:
    """RAG 검색 tool은 기준 확정 tool을 먼저 거치도록 agent 내부 순서를 맞춘다."""

    if intent == INTENT_RAG_ANSWER and tool_name in {
        TOOL_RETRIEVE_RAG,
        TOOL_COMPARE_SNAPSHOTS,
    }:
        return TOOL_RESOLVE_RAG_BASIS
    return tool_name


def route_after_tool(state: AgentGraphState) -> str:
    """tool 실행 후 다음 tool, LLM 답변 생성, 종료 중 하나로 그래프를 이동한다."""

    if state.get("tool_queue"):
        return "run_tool"
    if state.get("rag_response"):
        return "generate_answer"
    return "end"


def build_rag_next_tool_queue(state: AgentGraphState, target_runs: list[Any]) -> list[str]:
    """RAG 질문은 먼저 코드 근거 검색으로 보내고, tool 선택 판단은 LLM planner에 맡긴다."""

    return [state.get("planned_rag_tool_name") or TOOL_RETRIEVE_RAG]


def is_short_follow_up_selection(user_input: str) -> bool:
    """숫자 하나처럼 문맥 후보를 보고 해석해야 하는 짧은 후속 입력인지 본다."""

    text = normalize_text(user_input)
    stripped_number = text.replace("번", "").replace(".", "").strip()
    return stripped_number.isdigit() or text in {"그거", "이거", "위에거"}


def is_intent_resolver_fallback(intent_plan: Any) -> bool:
    """LLM intent resolver가 실패해서 기본값을 돌려준 상태인지 확인한다."""

    reason = getattr(intent_plan, "reason", None)
    return isinstance(reason, str) and reason.startswith(FALLBACK_REASON_PREFIX)


def resolve_basis_mode(
    user_input: str,
    current_refs: list[InferredRepositoryRef],
    fallback_mode: BasisMode,
) -> BasisMode:
    """명시적인 기준 변경 동사가 있으면 LLM의 basis_mode보다 사용자 문장을 우선한다."""

    if is_basis_change_request(user_input):
        return detect_basis_mode(user_input)
    if is_bare_target_selection(user_input) or is_branch_target_selection(user_input):
        return detect_bare_target_basis_mode(current_refs)
    return fallback_mode


def remove_last_basis_ref_if_short_request(
    user_input: str,
    current_refs: list[InferredRepositoryRef],
) -> list[InferredRepositoryRef]:
    """'빼', '다시 빼'처럼 대상이 없는 짧은 제거 요청은 마지막 기준 하나만 제거한다."""

    if is_short_remove_request(user_input) and current_refs:
        return current_refs[:-1]
    return current_refs


class SimpleIntentPlan:
    """intent resolver가 없을 때 쓰는 최소 fallback plan."""

    def __init__(self, intent: AgentIntent, basis_mode: BasisMode | None) -> None:
        self.intent = intent
        self.basis_mode = basis_mode
        self.reason = None


def build_remove_planner_input(user_input: str) -> str:
    """planner가 남길 기준이 아니라 제거할 기준을 고르도록 요청을 보강한다."""

    return (
        "현재 답변 기준 후보 중에서 제거할 대상만 골라라. "
        "남길 대상은 절대 고르지 마라. "
        f"사용자 요청: {user_input}"
    )


def detect_bare_target_basis_mode(
    current_refs: list[InferredRepositoryRef],
) -> BasisMode:
    """이미 기준이 있을 때 짧은 레포/브랜치 선택문은 기존 기준에 추가한다."""

    return BASIS_MODE_ADD if current_refs else BASIS_MODE_REPLACE


def has_explicit_target_hint(user_input: str) -> bool:
    """내용 질문 안에 레포/브랜치 대상 단서가 있으면 현재 기준보다 질문을 우선한다."""

    text = normalize_text(user_input)
    return "/" in text or "\\" in text or "브랜치" in text or "레포" in text
