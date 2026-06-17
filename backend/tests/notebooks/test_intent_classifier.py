"""의도 분류기(intent_classifier) 테스트.

모든 IntentType에 대해 키워드 휴리스틱이 올바르게 동작하는지,
should_skip_rag 판단이 정확한지 검증한다.
"""

import pytest

from app.notebooks.application.intent_classifier import (
    IntentType,
    classify_intent,
    should_skip_rag,
)

# ===================================================================
# classify_intent — CONVERSATIONAL
# ===================================================================


class TestConversational:
    """인사·잡담 의도 분류 테스트."""

    @pytest.mark.parametrize(
        "question",
        [
            "안녕",
            "안녕하세요",
            "반가워",
            "반갑습니다",
            "하이",
            "헬로",
            "hi",
            "hello",
            "Hello!",
            "Hey",
            "좋은 아침",
            "좋은 저녁",
            "감사합니다",
            "고마워",
            "ㅎㅇ",
            "ㅎㅎ",
            "ㅋㅋ",
        ],
    )
    def test_greeting_patterns(self, question: str) -> None:
        """인사 패턴은 CONVERSATIONAL로 분류된다."""
        assert classify_intent(question) == IntentType.CONVERSATIONAL

    def test_empty_string(self) -> None:
        """빈 문자열은 CONVERSATIONAL로 분류된다."""
        assert classify_intent("") == IntentType.CONVERSATIONAL

    def test_whitespace_only(self) -> None:
        """공백만 있는 문자열도 CONVERSATIONAL로 분류된다."""
        assert classify_intent("   ") == IntentType.CONVERSATIONAL


# ===================================================================
# classify_intent — BUG_ANALYSIS
# ===================================================================


class TestBugAnalysis:
    """버그·에러 분석 의도 분류 테스트."""

    @pytest.mark.parametrize(
        "question",
        [
            "이 코드에서 버그를 찾아줘",
            "에러가 발생합니다",
            "오류 원인이 뭔가요?",
            "TypeError exception이 나와요",
            "traceback을 분석해줘",
            "이 함수가 실패하는 이유",
            "debug 방법을 알려줘",
            "crash가 발생해요",
            "이 문제 좀 봐줘",
            "fix해야 할 부분이 있나요",
        ],
    )
    def test_bug_keywords(self, question: str) -> None:
        """버그·에러 키워드가 있으면 BUG_ANALYSIS로 분류된다."""
        assert classify_intent(question) == IntentType.BUG_ANALYSIS


# ===================================================================
# classify_intent — ARCHITECTURE
# ===================================================================


class TestArchitecture:
    """아키텍처·구조 의도 분류 테스트."""

    @pytest.mark.parametrize(
        "question",
        [
            "프로젝트 구조를 설명해줘",
            "아키텍처가 어떻게 되어있나요?",
            "모듈 간 의존성을 보여줘",
            "디렉토리 구조가 궁금합니다",
            "계층 구조를 알려줘",
            "헥사고날 패턴을 따르나요?",
            "이 컴포넌트의 설계를 분석해줘",
            "clean architecture인가요?",
        ],
    )
    def test_architecture_keywords(self, question: str) -> None:
        """아키텍처·구조 키워드가 있으면 ARCHITECTURE로 분류된다."""
        assert classify_intent(question) == IntentType.ARCHITECTURE


# ===================================================================
# classify_intent — GENERAL_KNOWLEDGE
# ===================================================================


class TestGeneralKnowledge:
    """일반 개발 지식 의도 분류 테스트."""

    @pytest.mark.parametrize(
        "question",
        [
            "DFS 알고리즘을 설명해줘",
            "BFS와 DFS의 차이점",
            "퀵 정렬의 시간 복잡도는?",
            "이진 탐색 구현 방법",
            "해시 테이블이 뭔가요?",
            "스택과 큐의 차이",
            "다이나믹 프로그래밍이란?",
            "재귀 함수를 어떻게 짜나요",
            "빅오 표기법 설명",
            "연결 리스트 구현",
            "자료구조 추천해줘",
        ],
    )
    def test_general_knowledge_without_sources(self, question: str) -> None:
        """소스가 없을 때 CS 키워드는 GENERAL_KNOWLEDGE로 분류된다."""
        assert classify_intent(question, has_sources=False) == IntentType.GENERAL_KNOWLEDGE

    @pytest.mark.parametrize(
        "question",
        [
            "DFS 알고리즘을 설명해줘",
            "정렬 방법을 알려줘",
        ],
    )
    def test_general_knowledge_with_sources_falls_to_code_search(self, question: str) -> None:
        """소스가 있으면 CS 키워드도 CODE_SEARCH로 분류된다 (RAG 검색 시도)."""
        assert classify_intent(question, has_sources=True) == IntentType.CODE_SEARCH


# ===================================================================
# classify_intent — CODE_SEARCH (기본값)
# ===================================================================


class TestCodeSearch:
    """코드 검색 의도(기본값) 분류 테스트."""

    @pytest.mark.parametrize(
        "question",
        [
            "chat_service.py에서 ask 함수의 동작을 설명해줘",
            "이 파일의 코드를 분석해줘",
            "함수 구현을 보여줘",
            "이 클래스의 역할은?",
            "특별한 키워드가 없는 일반 질문입니다",
        ],
    )
    def test_default_code_search(self, question: str) -> None:
        """기본적으로 CODE_SEARCH로 분류된다."""
        assert classify_intent(question) == IntentType.CODE_SEARCH


# ===================================================================
# classify_intent — 우선순위 테스트
# ===================================================================


class TestPriority:
    """의도 분류 우선순위 검증."""

    def test_conversational_beats_bug(self) -> None:
        """인사 패턴이 버그 키워드보다 우선한다."""
        # "안녕" 으로 시작하므로 CONVERSATIONAL이 먼저 매칭
        assert classify_intent("안녕 에러 있어?") == IntentType.CONVERSATIONAL

    def test_bug_beats_architecture(self) -> None:
        """버그 키워드가 아키텍처 키워드보다 우선한다."""
        assert classify_intent("이 모듈에서 에러가 나요") == IntentType.BUG_ANALYSIS

    def test_bug_beats_general_knowledge(self) -> None:
        """버그 키워드가 일반 지식 키워드보다 우선한다."""
        assert (
            classify_intent("DFS 알고리즘에 버그가 있어요", has_sources=False)
            == IntentType.BUG_ANALYSIS
        )

    def test_architecture_beats_general_knowledge(self) -> None:
        """아키텍처 키워드가 일반 지식 키워드보다 우선한다."""
        assert (
            classify_intent("자료구조의 계층 구조를 설명해줘", has_sources=False)
            == IntentType.ARCHITECTURE
        )


# ===================================================================
# should_skip_rag
# ===================================================================


class TestShouldSkipRag:
    """RAG 검색 스킵 판단 테스트."""

    def test_conversational_always_skips(self) -> None:
        """CONVERSATIONAL은 소스 유무와 관계없이 항상 RAG를 건너뛴다."""
        assert should_skip_rag(IntentType.CONVERSATIONAL, has_sources=True) is True
        assert should_skip_rag(IntentType.CONVERSATIONAL, has_sources=False) is True

    def test_general_knowledge_skips_without_sources(self) -> None:
        """GENERAL_KNOWLEDGE는 소스가 없을 때만 RAG를 건너뛴다."""
        assert should_skip_rag(IntentType.GENERAL_KNOWLEDGE, has_sources=False) is True

    def test_general_knowledge_does_not_skip_with_sources(self) -> None:
        """GENERAL_KNOWLEDGE라도 소스가 있으면 RAG를 수행한다."""
        assert should_skip_rag(IntentType.GENERAL_KNOWLEDGE, has_sources=True) is False

    @pytest.mark.parametrize(
        "intent",
        [IntentType.CODE_SEARCH, IntentType.ARCHITECTURE, IntentType.BUG_ANALYSIS],
    )
    def test_other_intents_never_skip(self, intent: IntentType) -> None:
        """CODE_SEARCH, ARCHITECTURE, BUG_ANALYSIS는 RAG를 건너뛰지 않는다."""
        assert should_skip_rag(intent, has_sources=True) is False
        assert should_skip_rag(intent, has_sources=False) is False


# ===================================================================
# classify_intent — 대소문자 무관 매칭
# ===================================================================


class TestCaseInsensitive:
    """키워드 매칭이 대소문자를 구분하지 않는지 검증."""

    def test_uppercase_bug_keyword(self) -> None:
        assert classify_intent("ERROR가 발생했습니다") == IntentType.BUG_ANALYSIS

    def test_mixed_case_architecture(self) -> None:
        assert classify_intent("Architecture를 분석하자") == IntentType.ARCHITECTURE

    def test_mixed_case_greeting(self) -> None:
        assert classify_intent("HELLO") == IntentType.CONVERSATIONAL
