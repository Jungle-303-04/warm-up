import re
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.domain.chat import (
    AgentTurnResult,
    ChatMessage,
    ChatSession,
    ChatTurn,
    InferredRepositoryRef,
)
from app.rag.api.schema import (
    RagAskRepositoryRefDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerUseCase, RagStore


AgentRoute = Literal["rag_answer", "direct_answer"]
RAG_ANSWER_ROUTE: AgentRoute = "rag_answer"
DIRECT_ANSWER_ROUTE: AgentRoute = "direct_answer"
REPOSITORY_NAME_PATTERN = re.compile(r"[\w.-]+/[\w.-]+")


class AgentGraphState(TypedDict, total=False):
    # 큰 agent graph가 공유하는 작업 메모리다.
    # 나중에 MCP action, board action, user confirmation state도 이 state에 추가한다.
    db: Session
    session: ChatSession
    messages: list[ChatMessage]
    turn: ChatTurn
    latest_runs: list[Any]
    inferred_repository_refs: list[InferredRepositoryRef] | None
    route: AgentRoute
    rag_response: RagAskResponseDTO
    final_answer: str


class AgentGraph:
    """RAG, MCP, 보드 작업을 한 대화 흐름에서 조립할 상위 AI graph."""

    def __init__(
        self,
        rag_answer_service: AnswerUseCase,
        sql_repository: RagStore,
    ) -> None:
        self.rag_answer_service = rag_answer_service
        self.sql_repository = sql_repository
        self.graph = self.build_graph()

    def run(
        self,
        db: Session,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> AgentTurnResult:
        """사용자 turn 하나를 큰 agent graph에 태워 답변과 추론 결과를 반환한다."""

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
            inferred_repository_refs=state.get("inferred_repository_refs"),
        )

    def build_graph(self):
        graph = StateGraph(AgentGraphState)

        # 현재 상위 graph는 최소 뼈대다.
        # plan_turn은 나중에 LLM planner로 교체하고, call_rag_answer는 RAG LangGraph를 노드처럼 호출한다.
        graph.add_node("collect_repository_context", self.collect_repository_context)
        graph.add_node("plan_turn", self.plan_turn)
        graph.add_node("call_rag_answer", self.call_rag_answer)
        graph.add_node("build_direct_answer", self.build_direct_answer)

        graph.set_entry_point("collect_repository_context")
        graph.add_edge("collect_repository_context", "plan_turn")
        graph.add_conditional_edges(
            "plan_turn",
            self.route_after_plan,
            {
                RAG_ANSWER_ROUTE: "call_rag_answer",
                DIRECT_ANSWER_ROUTE: "build_direct_answer",
            },
        )
        graph.add_edge("call_rag_answer", END)
        graph.add_edge("build_direct_answer", END)

        return graph.compile()

    def collect_repository_context(self, state: AgentGraphState) -> AgentGraphState:
        """agent가 답변 기준을 고를 수 있도록 최근 분석 run을 SQL에서 가져온다."""

        return {
            "latest_runs": [
                run
                for run in self.sql_repository.list_runs(state["db"], limit=50)
                if run.repository_full_name
            ],
        }

    def plan_turn(self, state: AgentGraphState) -> AgentGraphState:
        """사용자 입력에서 답변에 쓸 레포/브랜치를 고른다.

        지금은 명시적 owner/repo, repo 이름, branch 문자열을 이용한 최소 추론이다.
        TODO(agent): 이 노드를 LLM planner로 바꾸면 질문 의도, 여러 레포 선택,
        MCP action 필요 여부, 사용자 재질문 여부를 함께 결정할 수 있다.
        """

        inferred_repository_refs = infer_repository_refs(
            user_input=state["turn"].user_input,
            runs=state.get("latest_runs", []),
        )
        if inferred_repository_refs:
            return {
                "inferred_repository_refs": inferred_repository_refs,
                "route": RAG_ANSWER_ROUTE,
            }

        return {
            "inferred_repository_refs": None,
            "route": DIRECT_ANSWER_ROUTE,
        }

    def route_after_plan(self, state: AgentGraphState) -> AgentRoute:
        """planner가 고른 route에 따라 RAG 답변 또는 직접 안내로 분기한다."""

        return state.get("route", DIRECT_ANSWER_ROUTE)

    def call_rag_answer(self, state: AgentGraphState) -> AgentGraphState:
        """상위 agent graph 안에서 기존 RAG answer graph를 하나의 노드처럼 호출한다."""

        rag_request = RagAskRequestDTO(
            question=state["turn"].user_input,
            repository_refs=[
                to_rag_repository_ref(ref)
                for ref in state.get("inferred_repository_refs") or []
            ],
            limit=5,
        )
        rag_response = self.rag_answer_service.answer(state["db"], rag_request)
        return {
            "rag_response": rag_response,
            "final_answer": format_rag_agent_answer(rag_response),
        }

    def build_direct_answer(self, state: AgentGraphState) -> AgentGraphState:
        """RAG 기준을 고르지 못했을 때 사용자에게 다음 입력 방법을 안내한다."""

        latest_runs = state.get("latest_runs", [])
        if not latest_runs:
            return {
                "final_answer": (
                    "아직 답변에 사용할 레포지토리 분석 결과가 없습니다. "
                    "먼저 레포지토리를 등록하고 분석해 주세요."
                ),
            }

        examples = ", ".join(
            format_run_choice(run)
            for run in latest_runs[:3]
        )
        return {
            "final_answer": (
                "어떤 레포지토리 기준으로 답할지 아직 고르지 못했습니다. "
                f"질문에 레포지토리 이름이나 브랜치를 함께 적어 주세요. 예: {examples}"
            ),
        }


def infer_repository_refs(
    user_input: str,
    runs: list[Any],
) -> list[InferredRepositoryRef]:
    """질문에 언급된 레포/브랜치를 최근 분석 run의 정확한 commit 기준으로 바꾼다."""

    if not runs:
        return []

    normalized_input = normalize_text(user_input)
    mentioned_repositories = set(REPOSITORY_NAME_PATTERN.findall(normalized_input))
    scored_runs = [
        (run, score_run_mention(normalized_input, mentioned_repositories, run))
        for run in runs
    ]
    matched_runs = [
        (run, score)
        for run, score in scored_runs
        if score > 0
    ]

    if not matched_runs:
        unique_repositories = {normalize_text(run.repository_full_name) for run in runs}
        if len(unique_repositories) == 1:
            return [build_inferred_repository_ref(runs[0])]
        return []

    highest_score = max(score for _, score in matched_runs)
    best_runs = [run for run, score in matched_runs if score == highest_score]
    latest_runs = get_latest_runs_by_repository_and_branch(
        best_runs,
        keep_branch=highest_score >= 50,
    )

    return [build_inferred_repository_ref(run) for run in latest_runs]


def score_run_mention(
    normalized_input: str,
    mentioned_repositories: set[str],
    run: Any,
) -> int:
    repository_full_name = normalize_text(run.repository_full_name)
    repository_name = normalize_text(str(run.repository_full_name or "").split("/")[-1])
    branch = normalize_text(run.branch)

    has_full_repository = (
        repository_full_name in mentioned_repositories
        or repository_full_name in normalized_input
    )
    has_repository_name = bool(repository_name and repository_name in normalized_input)
    has_branch = bool(branch and branch in normalized_input)

    if has_full_repository and has_branch:
        return 60
    if has_repository_name and has_branch:
        return 50
    if has_full_repository:
        return 40
    if has_repository_name:
        return 30
    if has_branch:
        return 20
    return 0


def get_latest_runs_by_repository_and_branch(
    runs: list[Any],
    keep_branch: bool,
) -> list[Any]:
    latest_runs: dict[str, Any] = {}

    for run in runs:
        repository = normalize_text(run.repository_full_name)
        branch = normalize_text(run.branch)
        key = f"{repository}:{branch}" if keep_branch else repository
        current = latest_runs.get(key)
        if current is None or run.id > current.id:
            latest_runs[key] = run

    return list(latest_runs.values())


def build_inferred_repository_ref(run: Any) -> InferredRepositoryRef:
    """최신 run 선택 결과를 프론트에 돌려줄 추론 결과로 바꾼다."""

    return InferredRepositoryRef(
        run_id=run.id,
        repository_full_name=run.repository_full_name,
        branch=run.branch,
        commit_sha=run.commit_sha,
    )


def to_rag_repository_ref(ref: InferredRepositoryRef) -> RagAskRepositoryRefDTO:
    """agent 추론 결과를 RAG answer graph가 받는 요청 DTO로 바꾼다."""

    return RagAskRepositoryRefDTO(
        repository_full_name=ref.repository_full_name,
        branch=ref.branch,
        commit_sha=ref.commit_sha,
    )


def format_rag_agent_answer(response: RagAskResponseDTO) -> str:
    basis = "\n".join(
        format_response_ref(ref)
        for ref in response.repository_refs
        if ref.repository_full_name
    )
    sources = "\n".join(
        f"{index + 1}. {source.citation or source.path or '출처 정보 없음'}"
        for index, source in enumerate(response.sources[:5])
    )

    answer = response.answer
    if basis:
        answer = f"답변에 사용한 분석 결과\n{basis}\n\n{answer}"
    if sources:
        answer = f"{answer}\n\n출처\n{sources}"
    return answer


def format_response_ref(ref: Any) -> str:
    branch = ref.branch or "기본 브랜치"
    version = f" · 코드 버전 {ref.commit_sha[:7]}" if ref.commit_sha else ""
    return f"{ref.repository_full_name} · {branch}{version}"


def format_run_choice(run: Any) -> str:
    branch = run.branch or "기본 브랜치"
    return f"{run.repository_full_name} {branch}"


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()
