"""AnswerPlanner가 질문을 올바른 실행 경로로 라우팅하는지 검증한다."""

from app.notebooks.application.answer_planner import (
    AnswerRoute,
    DeterministicAnswerPlanner,
)
from app.notebooks.application.intent_classifier import IntentType
from app.notebooks.application.search_planner import SearchStrategy


def _planner() -> DeterministicAnswerPlanner:
    return DeterministicAnswerPlanner(default_top_k=5, architecture_top_k=8)


def test_routes_conversation_to_direct_answer() -> None:
    plan = _planner().plan("안녕하세요", has_sources=True, source_count=3)

    assert plan.route == AnswerRoute.DIRECT
    assert plan.intent == IntentType.CONVERSATIONAL
    assert plan.search_plan is None
    assert plan.preferred_tools == ()


def test_routes_commit_history_to_repo_facts() -> None:
    plan = _planner().plan("마지막 커밋 이력이 뭐야?", has_sources=True, source_count=2)

    assert plan.route == AnswerRoute.COMMIT_HISTORY
    assert plan.reason == "repo_commit_history"
    assert plan.search_plan is None


def test_routes_repo_overview_to_repo_snapshot_facts() -> None:
    plan = _planner().plan("이 레포 어떤 프로젝트야?", has_sources=True, source_count=1)

    assert plan.route == AnswerRoute.REPO_OVERVIEW
    assert plan.reason == "repo_overview"
    assert plan.search_plan is None


def test_architecture_question_is_not_misrouted_to_overview() -> None:
    plan = _planner().plan("이 레포 프로젝트 구조를 설명해줘", has_sources=True, source_count=5)

    assert plan.route == AnswerRoute.RAG
    assert plan.intent == IntentType.ARCHITECTURE


def test_routes_repo_question_to_rag_search_plan() -> None:
    plan = _planner().plan(
        "validate_session_token 함수는 어디 있어?",
        has_sources=True,
        source_count=4,
    )

    assert plan.route == AnswerRoute.RAG
    assert plan.search_plan is not None
    assert plan.search_plan.strategy == SearchStrategy.HYBRID
    assert "validate_session_token" in plan.search_plan.queries
    assert plan.preferred_tools == ("search_indexed_code", "find_symbol")


def test_routes_architecture_question_with_architecture_budget() -> None:
    plan = _planner().plan("프로젝트 구조를 설명해줘", has_sources=True, source_count=20)

    assert plan.route == AnswerRoute.RAG
    assert plan.intent == IntentType.ARCHITECTURE
    assert plan.search_plan is not None
    assert plan.search_plan.top_k == 8
    assert plan.preferred_tools == ("search_indexed_code",)


def test_file_path_question_prefers_file_read_tool() -> None:
    plan = _planner().plan(
        "backend/app/main.py 파일 전체를 읽고 설명해줘",
        has_sources=True,
        source_count=3,
    )

    assert plan.route == AnswerRoute.RAG
    assert "read_source_file" in plan.preferred_tools


def test_bug_question_prefers_search_symbol_and_file_read_tools() -> None:
    plan = _planner().plan(
        "login_user()에서 TypeError가 나는데 원인을 찾아줘",
        has_sources=True,
        source_count=3,
    )

    assert plan.route == AnswerRoute.RAG
    assert plan.intent == IntentType.BUG_ANALYSIS
    assert plan.preferred_tools == (
        "search_indexed_code",
        "find_symbol",
        "read_source_file",
    )
