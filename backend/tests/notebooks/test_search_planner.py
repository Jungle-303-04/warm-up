"""SearchPlanner 단위 테스트.

plan_search()가 의도별로 올바른 전략·쿼리·top_k를 생성하는지 검증한다.
"""

import pytest

from app.notebooks.application.search_planner import (
    SearchPlan,
    SearchStrategy,
    _extract_code_identifiers,
    _extract_error_keywords,
    plan_search,
)

# ================================================================== #
#  전략 선택 테스트
# ================================================================== #


class TestStrategySelection:
    """의도별로 올바른 SearchStrategy가 선택되는지 테스트한다."""

    def test_code_search_uses_hybrid(self):
        plan = plan_search("find_user 함수는 어디에 있나요?", "CODE_SEARCH", 10)
        assert plan.strategy == SearchStrategy.HYBRID

    def test_architecture_uses_hybrid(self):
        plan = plan_search("전체 시스템 아키텍처를 설명해줘", "ARCHITECTURE", 10)
        assert plan.strategy == SearchStrategy.HYBRID

    def test_bug_analysis_uses_hybrid(self):
        plan = plan_search("TypeError가 발생합니다", "BUG_ANALYSIS", 10)
        assert plan.strategy == SearchStrategy.HYBRID

    def test_general_knowledge_uses_vector_only(self):
        plan = plan_search("Python의 GIL이란?", "GENERAL_KNOWLEDGE", 10)
        assert plan.strategy == SearchStrategy.VECTOR_ONLY

    def test_conversational_uses_vector_only(self):
        plan = plan_search("안녕하세요", "CONVERSATIONAL", 10)
        assert plan.strategy == SearchStrategy.VECTOR_ONLY

    def test_unknown_intent_falls_back_to_general(self):
        plan = plan_search("뭔가 궁금해요", "UNKNOWN_INTENT", 10)
        assert plan.strategy == SearchStrategy.VECTOR_ONLY

    def test_case_insensitive_intent(self):
        plan = plan_search("find_user 함수", "code_search", 10)
        assert plan.strategy == SearchStrategy.HYBRID


# ================================================================== #
#  top_k 테스트
# ================================================================== #


class TestTopK:
    """의도·소스 수에 따라 top_k가 올바르게 설정되는지 테스트한다."""

    def test_architecture_gets_higher_top_k(self):
        plan = plan_search("프로젝트 구조를 알려줘", "ARCHITECTURE", 20)
        assert plan.top_k == 8

    def test_architecture_top_k_capped_by_source_count(self):
        plan = plan_search("구조", "ARCHITECTURE", 3)
        assert plan.top_k == 3

    def test_code_search_default_top_k(self):
        plan = plan_search("find_user 함수", "CODE_SEARCH", 20)
        assert plan.top_k == 5

    def test_code_search_top_k_capped_by_source_count(self):
        plan = plan_search("find_user 함수", "CODE_SEARCH", 2)
        assert plan.top_k == 2

    def test_general_lower_top_k(self):
        plan = plan_search("Python이란?", "GENERAL_KNOWLEDGE", 20)
        assert plan.top_k == 3

    def test_general_top_k_capped_by_source_count(self):
        plan = plan_search("Python이란?", "GENERAL_KNOWLEDGE", 1)
        assert plan.top_k == 1

    def test_zero_source_count_yields_1(self):
        """소스가 0개여도 top_k는 최소 1."""
        plan = plan_search("뭔가", "GENERAL_KNOWLEDGE", 0)
        assert plan.top_k == 1


# ================================================================== #
#  쿼리 생성 테스트
# ================================================================== #


class TestQueryGeneration:
    """의도별 서브쿼리가 올바르게 생성되는지 테스트한다."""

    def test_code_search_includes_original_query(self):
        plan = plan_search("find_user 함수", "CODE_SEARCH", 10)
        assert plan.queries[0] == "find_user 함수"

    def test_code_search_extracts_snake_case(self):
        plan = plan_search("find_user 함수는 뭐하나요?", "CODE_SEARCH", 10)
        assert "find_user" in plan.queries

    def test_code_search_extracts_camel_case(self):
        plan = plan_search("UserService 클래스를 찾아줘", "CODE_SEARCH", 10)
        assert "UserService" in plan.queries

    def test_code_search_extracts_dot_path(self):
        plan = plan_search("app.service.user에서 에러", "CODE_SEARCH", 10)
        assert "app.service.user" in plan.queries

    def test_code_search_no_duplicate_queries(self):
        plan = plan_search("find_user find_user", "CODE_SEARCH", 10)
        # 원본 + find_user 서브쿼리, 중복 없어야 함
        assert len(plan.queries) == len(set(plan.queries))

    def test_bug_analysis_extracts_error_keywords(self):
        plan = plan_search("TypeError: 'NoneType' object", "BUG_ANALYSIS", 10)
        assert "TypeError" in plan.queries

    def test_bug_analysis_extracts_http_codes(self):
        plan = plan_search("500 에러가 발생합니다", "BUG_ANALYSIS", 10)
        assert "500" in plan.queries

    def test_bug_analysis_includes_original_query(self):
        plan = plan_search("ValueError 발생", "BUG_ANALYSIS", 10)
        assert plan.queries[0] == "ValueError 발생"

    def test_general_single_query(self):
        plan = plan_search("Python GIL이란?", "GENERAL_KNOWLEDGE", 10)
        assert plan.queries == ["Python GIL이란?"]

    def test_architecture_single_query(self):
        plan = plan_search("전체 구조", "ARCHITECTURE", 10)
        assert plan.queries == ["전체 구조"]


# ================================================================== #
#  부스트 경로 테스트
# ================================================================== #


class TestBoostFilePaths:
    """boost_file_paths가 올바르게 설정되는지 테스트한다."""

    def test_default_no_boost(self):
        plan = plan_search("find_user", "CODE_SEARCH", 10)
        assert plan.boost_file_paths is None

    def test_general_no_boost(self):
        plan = plan_search("안녕", "CONVERSATIONAL", 10)
        assert plan.boost_file_paths is None


# ================================================================== #
#  내부 유틸 직접 테스트
# ================================================================== #


class TestExtractCodeIdentifiers:
    """_extract_code_identifiers가 다양한 패턴을 올바르게 추출하는지 테스트한다."""

    def test_camel_case(self):
        result = _extract_code_identifiers("UserService에서 에러 발생")
        assert "UserService" in result

    def test_snake_case(self):
        result = _extract_code_identifiers("get_user_by_id 함수")
        assert "get_user_by_id" in result

    def test_dot_path(self):
        result = _extract_code_identifiers("app.models.User 확인")
        assert "app.models.User" in result

    def test_function_call(self):
        result = _extract_code_identifiers("process_data() 호출 시")
        assert "process_data" in result

    def test_empty_string(self):
        result = _extract_code_identifiers("")
        assert result == []

    def test_no_identifiers(self):
        result = _extract_code_identifiers("안녕하세요 반갑습니다")
        assert result == []


class TestExtractErrorKeywords:
    """_extract_error_keywords가 에러 관련 키워드를 올바르게 추출하는지 테스트한다."""

    def test_exception_name(self):
        result = _extract_error_keywords("AttributeError 발생")
        assert "AttributeError" in result

    def test_http_status_code(self):
        result = _extract_error_keywords("404 에러")
        assert "404" in result

    def test_multiple_errors(self):
        result = _extract_error_keywords("TypeError와 ValueError 동시 발생")
        assert "TypeError" in result
        assert "ValueError" in result

    def test_case_insensitive(self):
        result = _extract_error_keywords("traceback이 보입니다")
        assert any(kw.lower() == "traceback" for kw in result)

    def test_no_errors(self):
        result = _extract_error_keywords("함수 호출 방법")
        assert result == []


# ================================================================== #
#  SearchPlan 불변성 테스트
# ================================================================== #


class TestSearchPlanImmutability:
    """SearchPlan이 frozen dataclass로 불변인지 테스트한다."""

    def test_frozen(self):
        plan = SearchPlan(
            strategy=SearchStrategy.HYBRID,
            queries=["test"],
            top_k=5,
        )
        with pytest.raises(AttributeError):
            plan.strategy = SearchStrategy.VECTOR_ONLY  # type: ignore[misc]


# ================================================================== #
#  SearchStrategy 열거형 테스트
# ================================================================== #


class TestSearchStrategy:
    """SearchStrategy enum 값이 올바른지 테스트한다."""

    def test_all_values(self):
        assert SearchStrategy.VECTOR_ONLY.value == "vector_only"
        assert SearchStrategy.KEYWORD_ONLY.value == "keyword_only"
        assert SearchStrategy.HYBRID.value == "hybrid"
        assert SearchStrategy.MULTI_QUERY.value == "multi_query"

    def test_member_count(self):
        assert len(SearchStrategy) == 4
