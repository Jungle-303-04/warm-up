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
    INTENT_SHOW_BASIS,
    AgentIntent,
    BasisMode,
    detect_basis_mode,
    has_path_focus_hint,
    is_general_chat,
    is_basis_change_request,
    is_branch_list_question,
    is_bare_target_selection,
    is_current_basis_question,
    is_file_list_question,
    is_repository_list_question,
    is_short_remove_request,
    normalize_text,
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
    build_evidence_fallback_answer,
    build_no_evidence_answer,
    get_message_content,
)
from app.agent.service.repository_context import (
    build_basis_changed_answer,
    build_branch_list_answer,
    build_available_path_prefixes,
    build_clarification_answer,
    build_current_basis_answer,
    build_file_snapshot_comparison_answer,
    build_file_list_answer,
    build_inferred_repository_ref,
    build_next_basis_refs,
    build_repository_list_answer,
    get_latest_unique_runs_by_repository_branch,
    is_snapshot_comparison_question,
    resolve_runs_from_refs,
    resolve_runs_from_recent_list_ordinal,
    resolve_runs_from_text,
    resolve_single_repository_fallback,
)
from app.rag.api.schema import (
    RagAskRepositoryRefDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerUseCase, RagStore


GENERAL_CHAT_SYSTEM_PROMPT = (
    "You are a Korean coding assistant for a code-trust kanban service. "
    "Respond naturally and briefly. Do not invent repository facts. "
    "If the user seems to need repository/code analysis, suggest asking for the repository list "
    "or naming a repository."
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
        graph.add_node("answer_repository_metadata", self.answer_repository_metadata)
        graph.add_node("answer_repository_files", self.answer_repository_files)
        graph.add_node("answer_repository_comparison", self.answer_repository_comparison)
        graph.add_node("change_repository_basis", self.change_repository_basis)
        graph.add_node("resolve_rag_basis", self.resolve_rag_basis)
        graph.add_node("retrieve_rag", self.retrieve_rag)
        graph.add_node("generate_answer", self.generate_answer)
        graph.add_node("answer_general_chat", self.answer_general_chat)
        graph.add_node("ask_clarification", self.ask_clarification)

        graph.set_entry_point("collect_repository_context")
        graph.add_edge("collect_repository_context", "classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            route_intent,
            {
                INTENT_LIST_REPOSITORIES: "answer_repository_metadata",
                INTENT_LIST_BRANCHES: "answer_repository_metadata",
                INTENT_LIST_FILES: "answer_repository_files",
                INTENT_SHOW_BASIS: "answer_repository_metadata",
                INTENT_CHANGE_BASIS: "change_repository_basis",
                INTENT_RAG_ANSWER: "resolve_rag_basis",
                INTENT_GENERAL_CHAT: "answer_general_chat",
                INTENT_CLARIFY: "ask_clarification",
            },
        )
        graph.add_conditional_edges(
            "resolve_rag_basis",
            route_resolved_rag_basis,
            {
                "retrieve": "retrieve_rag",
                "compare": "answer_repository_comparison",
                "clarify": "ask_clarification",
            },
        )
        graph.add_edge("retrieve_rag", "generate_answer")
        graph.add_edge("answer_repository_metadata", END)
        graph.add_edge("answer_repository_files", END)
        graph.add_edge("answer_repository_comparison", END)
        graph.add_edge("change_repository_basis", END)
        graph.add_edge("generate_answer", END)
        graph.add_edge("answer_general_chat", END)
        graph.add_edge("ask_clarification", END)

        return graph.compile()

    def collect_repository_context(self, state: AgentGraphState) -> AgentGraphState:
        """SQL에 저장된 최신 레포/브랜치별 분석 run만 모아 다음 노드에 넘긴다."""

        return {
            "latest_runs": get_latest_unique_runs_by_repository_branch(
                self.sql_repository.list_runs(state["db"], limit=100)
            )
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
                intent=correct_intent_with_explicit_markers(user_input, intent_plan.intent),
                basis_mode=intent_plan.basis_mode or BASIS_MODE_REPLACE,
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
        user_input: str,
        latest_runs: list[Any],
        current_refs: list[InferredRepositoryRef],
        messages: list[ChatMessage],
    ) -> AgentGraphState:
        """분류된 intent를 LangGraph state로 바꾼다."""

        if intent == INTENT_CHANGE_BASIS and is_bare_target_selection(user_input):
            basis_mode = detect_bare_target_basis_mode(current_refs)

        if intent == INTENT_LIST_REPOSITORIES:
            return {"intent": INTENT_LIST_REPOSITORIES}
        if intent == INTENT_LIST_BRANCHES:
            return {
                "intent": INTENT_LIST_BRANCHES,
                "target_runs": self.resolve_target_runs(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            }
        if intent == INTENT_SHOW_BASIS:
            return {"intent": INTENT_SHOW_BASIS}
        if intent == INTENT_GENERAL_CHAT:
            return {"intent": INTENT_GENERAL_CHAT}
        if intent == INTENT_LIST_FILES:
            return {
                "intent": INTENT_LIST_FILES,
                "target_runs": self.resolve_runs_for_current_question(
                    user_input=user_input,
                    latest_runs=latest_runs,
                    current_refs=current_refs,
                    messages=messages,
                ),
            }
        if intent == INTENT_CHANGE_BASIS:
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

    def answer_repository_metadata(self, state: AgentGraphState) -> AgentGraphState:
        """레포 목록, 브랜치 목록, 현재 기준은 RAG 없이 SQL 메타데이터만으로 답한다."""

        intent = state["intent"]
        latest_runs = state.get("latest_runs", [])
        current_refs = list(state["turn"].repository_refs)

        if intent == INTENT_LIST_REPOSITORIES:
            final_answer = build_repository_list_answer(latest_runs)
        elif intent == INTENT_LIST_BRANCHES:
            final_answer = build_branch_list_answer(
                user_input=state["turn"].user_input,
                latest_runs=latest_runs,
                target_runs=state.get("target_runs", []),
                current_refs=current_refs,
                messages=state.get("messages", []),
            )
        else:
            final_answer = build_current_basis_answer(current_refs)

        return {
            "final_answer": final_answer,
            "final_refs": current_refs,
            "repository_basis_changed": False,
        }

    def answer_repository_files(self, state: AgentGraphState) -> AgentGraphState:
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

    def answer_repository_comparison(self, state: AgentGraphState) -> AgentGraphState:
        """두 개 이상의 선택 기준은 SQL 파일 스냅샷으로 먼저 구조적 차이를 답한다."""

        target_runs = state.get("target_runs", [])
        file_snapshots_by_run = {
            run.id: self.sql_repository.list_file_snapshots(state["db"], run.id)
            for run in target_runs
        }
        final_refs = [build_inferred_repository_ref(run) for run in target_runs]
        return {
            "final_answer": build_file_snapshot_comparison_answer(
                target_runs=target_runs,
                file_snapshots_by_run=file_snapshots_by_run,
            ),
            "final_refs": final_refs,
            "repository_basis_changed": bool(final_refs),
        }

    def change_repository_basis(self, state: AgentGraphState) -> AgentGraphState:
        """사용자가 지정한 레포 이름을 SQL run에 매핑해 다음 답변 기준으로 저장한다."""

        current_refs = list(state["turn"].repository_refs)
        target_runs = state.get("target_runs", [])
        mode = state.get("basis_mode", BASIS_MODE_REPLACE)

        if mode == BASIS_MODE_REMOVE and not target_runs and current_refs:
            return {
                "final_answer": build_basis_changed_answer([], BASIS_MODE_CLEAR),
                "final_refs": [],
                "repository_basis_changed": True,
            }

        final_refs = build_next_basis_refs(
            current_refs=current_refs,
            target_runs=target_runs,
            mode=mode,
        )

        if mode != BASIS_MODE_CLEAR and not target_runs:
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

    def resolve_rag_basis(self, state: AgentGraphState) -> AgentGraphState:
        """RAG 검색 전에 질문이 어떤 분석 run을 기준으로 삼는지 확정한다."""

        current_refs = list(state["turn"].repository_refs)
        if current_refs:
            return {
                "target_runs": resolve_runs_from_refs(current_refs, state.get("latest_runs", [])),
                "final_refs": current_refs,
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
            }

        single_run = resolve_single_repository_fallback(state.get("latest_runs", []))
        if single_run is not None:
            return {
                "target_runs": [single_run],
                "final_refs": [build_inferred_repository_ref(single_run)],
                "repository_basis_changed": True,
            }

        return {
            "target_runs": [],
            "final_refs": current_refs,
        }

    def retrieve_rag(self, state: AgentGraphState) -> AgentGraphState:
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
                question=state["turn"].user_input,
                repository_refs=refs,
                limit=5,
            ),
        )
        return {"rag_response": rag_response}

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

    def answer_general_chat(self, state: AgentGraphState) -> AgentGraphState:
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

    def ask_clarification(self, state: AgentGraphState) -> AgentGraphState:
        """검색 기준을 확정하지 못했을 때 가능한 레포 예시를 보여준다."""

        return {
            "final_answer": build_clarification_answer(state.get("latest_runs", [])),
            "final_refs": list(state["turn"].repository_refs),
            "repository_basis_changed": False,
        }


def route_intent(state: AgentGraphState) -> AgentIntent:
    return state.get("intent", INTENT_CLARIFY)


def route_resolved_rag_basis(state: AgentGraphState) -> str:
    if state.get("target_runs"):
        if (
            len(state.get("target_runs", [])) >= 2
            and is_snapshot_comparison_question(state["turn"].user_input)
        ):
            return "compare"
        return "retrieve"
    return "clarify"


def is_short_follow_up_selection(user_input: str) -> bool:
    """숫자 하나처럼 문맥 후보를 보고 해석해야 하는 짧은 후속 입력인지 본다."""

    text = normalize_text(user_input)
    stripped_number = text.replace("번", "").replace(".", "").strip()
    return stripped_number.isdigit() or text in {"그거", "이거", "위에거"}


def is_intent_resolver_fallback(intent_plan: Any) -> bool:
    """LLM intent resolver가 실패해서 기본값을 돌려준 상태인지 확인한다."""

    reason = getattr(intent_plan, "reason", None)
    return isinstance(reason, str) and reason.startswith(FALLBACK_REASON_PREFIX)


def correct_intent_with_explicit_markers(
    user_input: str,
    intent: AgentIntent,
) -> AgentIntent:
    """LLM intent가 명시적인 파일/브랜치 표현과 충돌하면 안전한 쪽으로 보정한다."""

    if is_bare_target_selection(user_input):
        return INTENT_CHANGE_BASIS
    if is_basis_change_request(user_input):
        return INTENT_CHANGE_BASIS
    if is_file_list_question(user_input):
        return INTENT_LIST_FILES
    if is_branch_list_question(user_input):
        return INTENT_LIST_BRANCHES
    if is_repository_list_question(user_input):
        return INTENT_LIST_REPOSITORIES
    return intent


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
