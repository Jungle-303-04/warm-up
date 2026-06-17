"""검색 계획 수립 모듈.

질문의 의도(intent_type)와 소스 수에 따라 최적의 검색 전략을 결정하고,
필요 시 서브 쿼리를 생성한다. chat_service가 이 모듈의 SearchPlan을 사용하여
다중 전략 검색을 수행할 수 있다.
"""

import re
from dataclasses import dataclass, field
from enum import Enum

# ---- 코드 식별자 추출 패턴 ---- #
# CamelCase, snake_case, 점(.)으로 구분된 식별자 등을 잡는다.
# 한국어가 바로 뒤에 올 수 있으므로 \b 대신 명시적 ASCII 경계를 사용한다.
_CAMEL_RE = re.compile(r"(?<![A-Za-z])([A-Z][a-z]+(?:[A-Z][a-z]+)+)(?![A-Za-z])")
_SNAKE_RE = re.compile(r"(?<![A-Za-z0-9_])([a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?![A-Za-z0-9_])")
_DOT_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.])([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)(?![A-Za-z0-9_.])")
_FUNC_CALL_RE = re.compile(r"(?<![A-Za-z0-9_])([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")

# 에러 키워드 추출 패턴 — 한국어 접미사가 붙어도 인식한다.
_ERROR_KW_RE = re.compile(
    r"(?<![A-Za-z])(Error|Exception|Traceback|FAIL|FAILED|TypeError|ValueError|KeyError"
    r"|AttributeError|ImportError|RuntimeError|IndexError|FileNotFoundError"
    r"|NameError|OSError|IOError|ZeroDivisionError|StopIteration)(?![A-Za-z])",
    re.IGNORECASE,
)
_HTTP_CODE_RE = re.compile(r"(?<!\d)([45]\d{2})(?!\d)")


class SearchStrategy(Enum):
    """검색 전략 열거형."""

    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"
    MULTI_QUERY = "multi_query"


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """검색 계획 – 전략, 쿼리 목록, top_k, 부스트 경로를 포함한다."""

    strategy: SearchStrategy
    queries: list[str]
    top_k: int = 5
    boost_file_paths: list[str] | None = None


_DEFAULT_TOP_K = 5
_ARCHITECTURE_TOP_K = 8


def plan_search(
    question: str,
    intent_type: str,
    source_count: int,
    *,
    default_top_k: int = _DEFAULT_TOP_K,
    architecture_top_k: int = _ARCHITECTURE_TOP_K,
) -> SearchPlan:
    """질문·의도·소스 수를 기반으로 검색 계획을 수립한다.

    top_k 상한(default_top_k/architecture_top_k)은 Settings(.env)에서 주입되며,
    기본값은 모듈 상수로 폴백한다(직접 호출/단위 테스트 호환).

    Parameters
    ----------
    question:
        사용자 질문 원문(또는 재구성된 standalone 질문).
    intent_type:
        의도 분류 문자열. CODE_SEARCH, ARCHITECTURE, BUG_ANALYSIS,
        GENERAL_KNOWLEDGE, CONVERSATIONAL 등이 올 수 있다.
    source_count:
        노트북에 등록된 소스 수. 소스가 적으면 top_k를 줄인다.

    Returns
    -------
    SearchPlan
        검색 전략·쿼리 목록·top_k·부스트 경로가 담긴 계획.
    """
    normalized = intent_type.upper().replace(" ", "_")

    if normalized == "CODE_SEARCH":
        return _plan_code_search(question, source_count, default_top_k)
    if normalized == "ARCHITECTURE":
        return _plan_architecture(question, source_count, architecture_top_k)
    if normalized == "BUG_ANALYSIS":
        return _plan_bug_analysis(question, source_count, default_top_k)
    # GENERAL_KNOWLEDGE, CONVERSATIONAL, 그 외
    return _plan_general(question, source_count)


# ------------------------------------------------------------------ #
#  의도별 전략 계획
# ------------------------------------------------------------------ #


def _plan_code_search(question: str, source_count: int, top_k_cap: int) -> SearchPlan:
    """코드 검색: HYBRID + 코드 식별자 서브쿼리."""
    queries = [question]
    identifiers = _extract_code_identifiers(question)
    for ident in identifiers:
        sub = ident if ident != question else None
        if sub and sub not in queries:
            queries.append(sub)

    top_k = min(top_k_cap, max(source_count, 1))
    return SearchPlan(
        strategy=SearchStrategy.HYBRID,
        queries=queries,
        top_k=top_k,
    )


def _plan_architecture(question: str, source_count: int, top_k_cap: int) -> SearchPlan:
    """아키텍처 질문: HYBRID + 높은 top_k."""
    queries = [question]
    top_k = min(top_k_cap, max(source_count, 1))
    return SearchPlan(
        strategy=SearchStrategy.HYBRID,
        queries=queries,
        top_k=top_k,
    )


def _plan_bug_analysis(question: str, source_count: int, top_k_cap: int) -> SearchPlan:
    """버그/에러 분석: HYBRID + 에러 키워드 서브쿼리."""
    queries = [question]
    error_keywords = _extract_error_keywords(question)
    for kw in error_keywords:
        if kw not in queries:
            queries.append(kw)

    top_k = min(top_k_cap, max(source_count, 1))
    return SearchPlan(
        strategy=SearchStrategy.HYBRID,
        queries=queries,
        top_k=top_k,
    )


def _plan_general(question: str, source_count: int) -> SearchPlan:
    """일반 지식/대화: VECTOR_ONLY + 낮은 top_k."""
    top_k = min(3, max(source_count, 1))
    return SearchPlan(
        strategy=SearchStrategy.VECTOR_ONLY,
        queries=[question],
        top_k=top_k,
    )


# ------------------------------------------------------------------ #
#  유틸리티: 식별자·키워드 추출
# ------------------------------------------------------------------ #


def _extract_code_identifiers(text: str) -> list[str]:
    """질문에서 코드 식별자(함수명, 클래스명 등)를 추출한다."""
    found: list[str] = []
    seen: set[str] = set()

    for pattern in (_CAMEL_RE, _SNAKE_RE, _DOT_PATH_RE):
        for match in pattern.finditer(text):
            value = match.group()
            if value not in seen:
                seen.add(value)
                found.append(value)

    for match in _FUNC_CALL_RE.finditer(text):
        name = match.group(1)
        # 일반 영어 단어는 걸러낸다 (3글자 이하이면서 snake도 camel도 아닌 것)
        if name not in seen and (len(name) > 3 or "_" in name):
            seen.add(name)
            found.append(name)

    return found


def _extract_error_keywords(text: str) -> list[str]:
    """질문에서 에러/예외 관련 키워드를 추출한다."""
    found: list[str] = []
    seen: set[str] = set()

    for match in _ERROR_KW_RE.finditer(text):
        value = match.group()
        if value not in seen:
            seen.add(value)
            found.append(value)

    for match in _HTTP_CODE_RE.finditer(text):
        code = match.group()
        if code not in seen:
            seen.add(code)
            found.append(code)

    return found
