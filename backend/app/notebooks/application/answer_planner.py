"""채팅 답변 경로 결정기.

LLM이 바로 답할지, repo facts를 볼지, RAG 검색을 수행할지 결정한다. 실행은
ChatService가 담당하고, 이 모듈은 상태/의도에 따른 route와 검색 계획만 만든다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, unique
from typing import Literal, Protocol

from app.notebooks.application.intent_classifier import (
    IntentType,
    classify_intent,
    should_skip_rag,
)
from app.notebooks.application.search_planner import SearchPlan, plan_search

ToolName = Literal["search_indexed_code", "find_symbol", "read_source_file"]


@unique
class AnswerRoute(Enum):
    """채팅 요청이 통과할 실행 경로."""

    DIRECT = "direct"
    """RAG 없이 바로 답변한다. 인사/잡담/소스 없는 일반 지식에 사용."""

    COMMIT_HISTORY = "commit_history"
    """Git 저장소의 최근 커밋 facts를 사용해 답한다."""

    REPO_OVERVIEW = "repo_overview"
    """Git 저장소 메타데이터와 README snapshot으로 프로젝트 개요를 답한다."""

    RAG = "rag"
    """벡터/키워드 검색, 컨텍스트 확장, 도구 사용 경로를 탄다."""


@dataclass(frozen=True, slots=True)
class AnswerPlan:
    """질문 하나에 대한 실행 계획."""

    route: AnswerRoute
    intent: IntentType
    search_plan: SearchPlan | None = None
    preferred_tools: tuple[ToolName, ...] = ()
    reason: str = ""


class AnswerPlanner(Protocol):
    """질문과 현재 scope 상태를 받아 실행 계획을 만든다."""

    def plan(
        self,
        question: str,
        *,
        has_sources: bool,
        source_count: int,
    ) -> AnswerPlan: ...


_COMMIT_HISTORY_KEYWORDS = (
    "커밋",
    "commit",
    "git log",
    "최근 변경",
    "변경 이력",
    "마지막 변경",
    "last change",
    "latest change",
    "recent change",
)

_REPO_OVERVIEW_KEYWORDS = (
    "어떤 프로젝트",
    "무슨 프로젝트",
    "무슨 레포",
    "어떤 레포",
    "이 레포",
    "이 저장소",
    "프로젝트야",
    "레포야",
    "뭐 하는",
    "뭐하는",
    "소개",
    "overview",
    "about this repo",
    "what project",
)

_READ_FILE_CUES = (
    "파일 전체",
    "전체 파일",
    "원문",
    "직접 읽",
    "열어",
    "읽어",
    "read file",
    "open file",
    "entire file",
    "full file",
)

_SYMBOL_CUES = (
    "함수",
    "메서드",
    "메소드",
    "클래스",
    "심볼",
    "정의",
    "어디",
    "찾아",
    "function",
    "method",
    "class",
    "symbol",
    "definition",
    "where",
)

_FILE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_/.-])[\w./-]+(?:\.py|\.pyi|\.ts|\.tsx|\.js|\.jsx|\.sql|\.md|\.json|\.ya?ml|\.toml)(?![A-Za-z0-9_/.-])",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class DeterministicAnswerPlanner:
    """휴리스틱 기반의 기본 답변 planner.

    LangGraph/LLM planner가 필요한 복잡한 흐름과 달리, 일반 질문 라우팅은 빠르고
    검증 가능한 결정론 규칙으로 처리한다.
    """

    default_top_k: int
    architecture_top_k: int

    def plan(
        self,
        question: str,
        *,
        has_sources: bool,
        source_count: int,
    ) -> AnswerPlan:
        intent = classify_intent(question, has_sources=has_sources)
        if should_skip_rag(intent, has_sources=has_sources):
            return AnswerPlan(
                route=AnswerRoute.DIRECT,
                intent=intent,
                reason="rag_not_needed",
            )
        if _is_commit_history_question(question):
            return AnswerPlan(
                route=AnswerRoute.COMMIT_HISTORY,
                intent=intent,
                reason="repo_commit_history",
            )
        if _is_repo_overview_question(question):
            return AnswerPlan(
                route=AnswerRoute.REPO_OVERVIEW,
                intent=intent,
                reason="repo_overview",
            )
        search_plan = plan_search(
            question,
            intent_type=intent.value,
            source_count=source_count,
            default_top_k=self.default_top_k,
            architecture_top_k=self.architecture_top_k,
        )
        return AnswerPlan(
            route=AnswerRoute.RAG,
            intent=intent,
            search_plan=search_plan,
            preferred_tools=_preferred_tools(question, intent, search_plan),
            reason="rag_search",
        )


def _is_commit_history_question(question: str) -> bool:
    normalized = question.strip().lower()
    return any(keyword in normalized for keyword in _COMMIT_HISTORY_KEYWORDS)


def _is_repo_overview_question(question: str) -> bool:
    normalized = question.strip().lower()
    if "구조" in normalized or "architecture" in normalized:
        return False
    return any(keyword in normalized for keyword in _REPO_OVERVIEW_KEYWORDS)


def _preferred_tools(
    question: str,
    intent: IntentType,
    search_plan: SearchPlan,
) -> tuple[ToolName, ...]:
    """결정론 planner가 LLM에게 노출할 tool 후보를 좁힌다.

    실행 자체는 ChatService/ToolRegistry가 담당하지만, 어떤 종류의 도구가
    의미 있는지는 planner가 먼저 결정한다. 이렇게 하면 일반 RAG 질문에
    불필요한 파일 원문 읽기 도구를 열지 않고, 코드/버그 질문은 필요한 도구만
    제한적으로 노출할 수 있다.
    """
    tools: list[ToolName] = []

    def add(tool: ToolName) -> None:
        if tool not in tools:
            tools.append(tool)

    if intent in {
        IntentType.CODE_SEARCH,
        IntentType.BUG_ANALYSIS,
        IntentType.ARCHITECTURE,
    }:
        add("search_indexed_code")

    if intent in {IntentType.CODE_SEARCH, IntentType.BUG_ANALYSIS} and (
        len(search_plan.queries) > 1 or _has_symbol_cue(question)
    ):
        add("find_symbol")

    if _has_file_read_cue(question) or intent == IntentType.BUG_ANALYSIS:
        add("read_source_file")

    return tuple(tools)


def _has_symbol_cue(question: str) -> bool:
    normalized = question.strip().lower()
    return any(cue in normalized for cue in _SYMBOL_CUES)


def _has_file_read_cue(question: str) -> bool:
    normalized = question.strip().lower()
    return (
        any(cue in normalized for cue in _READ_FILE_CUES)
        or _FILE_PATH_RE.search(question) is not None
    )
