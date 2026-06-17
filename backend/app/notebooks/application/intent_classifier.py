"""질문 의도 분류 모듈.

사용자의 질문을 키워드 휴리스틱으로 분류하여 RAG 파이프라인의 흐름을
제어한다. LLM 호출 없이 빠르게 의도를 판별하므로 지연 시간이 거의 없다.

분류 결과(IntentType)에 따라 ChatService는 RAG 검색을 건너뛰거나,
프롬프트 전략을 달리 적용할 수 있다.
"""

from __future__ import annotations

import re
from enum import Enum, unique

# ---------------------------------------------------------------------------
# 의도 열거형
# ---------------------------------------------------------------------------


@unique
class IntentType(Enum):
    """사용자 질문의 의도 유형."""

    CODE_SEARCH = "code_search"
    """코드·파일 관련 질문 (기본값)."""

    ARCHITECTURE = "architecture"
    """프로젝트 구조·의존성·설계 관련 질문."""

    GENERAL_KNOWLEDGE = "general_knowledge"
    """일반 개발 지식 질문 (소스 컨텍스트 불필요)."""

    CONVERSATIONAL = "conversational"
    """인사·잡담 등 단순 대화."""

    BUG_ANALYSIS = "bug_analysis"
    """버그·에러·오류 분석 관련 질문."""


# ---------------------------------------------------------------------------
# 키워드 패턴 정의
# ---------------------------------------------------------------------------

# 인사·대화형 패턴 (문장 전체가 짧은 인사인 경우에 매칭)
_CONVERSATIONAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"^(안녕|반가워|반갑습니다|하이|헬로|hi|hello|hey|좋은\s*아침|"
        r"좋은\s*저녁|감사합니다|고마워|수고|잘\s*부탁|ㅎㅇ|ㅎㅎ|ㅋㅋ).*$",
        re.IGNORECASE,
    ),
]

# 버그·에러 분석 키워드
_BUG_KEYWORDS: list[str] = [
    "버그",
    "에러",
    "오류",
    "error",
    "bug",
    "exception",
    "traceback",
    "스택트레이스",
    "stack trace",
    "crash",
    "크래시",
    "디버그",
    "debug",
    "실패",
    "fail",
    "broken",
    "fix",
    "수정",
    "문제",
]

# 아키텍처·구조 키워드
_ARCHITECTURE_KEYWORDS: list[str] = [
    "프로젝트 구조",
    "코드 구조",
    "폴더 구조",
    "아키텍처",
    "architecture",
    "의존성",
    "dependency",
    "디렉토리",
    "directory",
    "폴더",
    "모듈",
    "module",
    "계층",
    "layer",
    "설계",
    "design",
    "컴포넌트",
    "component",
    "헥사고날",
    "hexagonal",
    "클린 아키텍처",
    "clean architecture",
]

# 일반 CS·개발 지식 키워드
_GENERAL_KNOWLEDGE_KEYWORDS: list[str] = [
    "알고리즘",
    "algorithm",
    "정렬",
    "sort",
    "dfs",
    "bfs",
    "이진 탐색",
    "binary search",
    "해시",
    "hash",
    "스택",
    "stack",
    "큐",
    "queue",
    "트리",
    "tree",
    "그래프",
    "graph",
    "다이나믹 프로그래밍",
    "dynamic programming",
    "dp",
    "재귀",
    "recursion",
    "시간 복잡도",
    "time complexity",
    "빅오",
    "big-o",
    "자료구조",
    "data structure",
    "linked list",
    "연결 리스트",
]

# 키워드를 소문자 정규화한 세트로 캐싱
_BUG_SET: frozenset[str] = frozenset(k.lower() for k in _BUG_KEYWORDS)
_ARCH_SET: frozenset[str] = frozenset(k.lower() for k in _ARCHITECTURE_KEYWORDS)
_GK_SET: frozenset[str] = frozenset(k.lower() for k in _GENERAL_KNOWLEDGE_KEYWORDS)



def _contains_any(text_lower: str, keywords: frozenset[str]) -> bool:
    """원문(소문자)에 키워드가 하나라도 포함되면 True.

    한국어는 교착어이므로 조사가 단어에 붙어 토큰 매칭이 어렵다
    (예: '에러가' → '에러' 토큰으로 분리되지 않음).
    따라서 모든 키워드를 부분 문자열 매칭으로 검사한다.
    """
    return any(kw in text_lower for kw in keywords)


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


def classify_intent(question: str, *, has_sources: bool = True) -> IntentType:
    """질문 텍스트를 분석하여 의도 유형을 반환한다.

    키워드 휴리스틱 기반이므로 LLM 호출이 필요하지 않다.
    우선순위: CONVERSATIONAL → BUG_ANALYSIS → ARCHITECTURE
    → GENERAL_KNOWLEDGE(소스 없을 때) → CODE_SEARCH(기본).

    Args:
        question: 사용자 질문 원문.
        has_sources: 현재 노트북에 연결된 소스가 있는지 여부.

    Returns:
        IntentType 열거값.
    """
    stripped = question.strip()
    if not stripped:
        return IntentType.CONVERSATIONAL

    text_lower = stripped.lower()

    # 1) 대화형 (짧은 인사)
    for pattern in _CONVERSATIONAL_PATTERNS:
        if pattern.match(stripped):
            return IntentType.CONVERSATIONAL

    # 2) 버그·에러 분석
    if _contains_any(text_lower, _BUG_SET):
        return IntentType.BUG_ANALYSIS

    # 3) 아키텍처·구조
    if _contains_any(text_lower, _ARCH_SET):
        return IntentType.ARCHITECTURE

    # 4) 일반 개발 지식 (소스가 없을 때만 — 소스가 있으면 CODE_SEARCH로
    #    RAG 검색을 통해 소스 기반 답변을 시도)
    if not has_sources and _contains_any(text_lower, _GK_SET):
        return IntentType.GENERAL_KNOWLEDGE

    # 5) 기본: 코드 검색
    return IntentType.CODE_SEARCH


def should_skip_rag(intent: IntentType, *, has_sources: bool = True) -> bool:
    """해당 의도에서 RAG 검색을 건너뛰어도 되는지 판단한다.

    CONVERSATIONAL은 항상 RAG 불필요.
    GENERAL_KNOWLEDGE는 소스 컨텍스트가 없을 때만 RAG 불필요.

    Args:
        intent: 분류된 의도 유형.
        has_sources: 현재 노트북에 연결된 소스가 있는지 여부.

    Returns:
        True이면 RAG 검색을 건너뛰어도 좋다.
    """
    if intent == IntentType.CONVERSATIONAL:
        return True
    return bool(intent == IntentType.GENERAL_KNOWLEDGE and not has_sources)
