"""노트북 애플리케이션 구성 요소 빌더.

이 파일은 상태/행위 구현체를 조립하는 위치를 명확히 하기 위한 composition root이다.
도메인 서비스는 포트에만 의존하고, 여기에서 설정값을 보고 어떤 infrastructure
adapter를 주입할지 결정한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.auth.domain.ports import GitHubTokenStore
from app.config import Settings
from app.notebooks.application.answer_planner import (
    AnswerPlanner,
    DeterministicAnswerPlanner,
)
from app.notebooks.domain.artifact_ports import LlmArtifactGenerator
from app.notebooks.infrastructure.artifact_generators import (
    ChatOpenAIArtifactGenerator,
    DeterministicArtifactGenerator,
)
from app.notebooks.infrastructure.github_commits import GitHubCommitFetcher

if TYPE_CHECKING:
    from app.notebooks.application.chat_service import (
        ChatAnswerer,
        CommitHistoryFetcher,
    )


def build_artifact_generator(settings: Settings) -> LlmArtifactGenerator:
    """설정에 맞는 artifact generator 구현체를 만든다."""

    if settings.llm_provider == "openai" and settings.openai_api_key:
        from app.pipeline.chat_models import build_chat_model

        chat_model = build_chat_model(
            settings.llm_provider,
            settings.llm_model,
            settings.openai_api_key,
            temperature=0.0,
        )
        return ChatOpenAIArtifactGenerator(chat_model)
    return DeterministicArtifactGenerator()


def build_chat_answerer(settings: Settings) -> ChatAnswerer | None:
    """설정에 맞는 채팅 답변기 구현체를 만든다."""

    if settings.llm_provider == "openai" and settings.openai_api_key:
        from app.notebooks.infrastructure.chat_answerers import (
            build_chat_openai_answerer,
        )

        return build_chat_openai_answerer(
            settings.llm_provider,
            settings.llm_model,
            settings.openai_api_key,
            temperature=0.0,
            use_tools=settings.chat_use_tools,
        )
    return None


def build_commit_history_fetcher(
    token_store: GitHubTokenStore,
) -> CommitHistoryFetcher:
    """GitHub 저장소 commit facts 조회 도구를 만든다."""

    return GitHubCommitFetcher(token_store)


def build_answer_planner(settings: Settings) -> AnswerPlanner:
    """설정 기반 deterministic planner를 만든다."""

    return DeterministicAnswerPlanner(
        default_top_k=settings.chat_default_top_k,
        architecture_top_k=settings.chat_architecture_top_k,
    )
