from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.agent.api.schema import (
    ChatSessionCreateRequestDTO,
    ChatSessionDetailResponseDTO,
    ChatSendMessageRequestDTO,
    ChatSendMessageResponseDTO,
)
from app.agent.domain.chat import (
    AgentTurnResult,
    ChatMessage,
    ChatSession,
    ChatTurn,
    InferredRepositoryRef,
)


class ChatStore(Protocol):
    """채팅 저장 방식을 메모리, SQL, Redis 등으로 교체하기 위한 저장소 계약."""

    def create_session(self, title: str | None) -> ChatSession: ...

    def get_session(self, session_id: str) -> ChatSession | None: ...

    def list_messages(self, session_id: str) -> list[ChatMessage]: ...

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> ChatMessage: ...


class AgentResponder(Protocol):
    """입력 turn과 이전 메시지를 받아 실제 답변을 만드는 에이전트 계약."""

    def answer(
        self,
        db: Session,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> AgentTurnResult: ...


class ToolCallingLlm(Protocol):
    """LangChain tool calling 모델을 AgentGraph가 교체 가능하게 쓰기 위한 계약."""

    def invoke(self, messages: list[Any], tools: list[Any]) -> Any: ...


class RepositoryTargetPlanResult(Protocol):
    """target planner가 고른 답변 기준 후보를 AgentGraph에 돌려주는 최소 계약."""

    inferred_repository_refs: list[InferredRepositoryRef] | None
    reason: str | None


class RepositoryTargetPlanner(Protocol):
    """사용자 질문과 분석 run 후보를 보고 답변 기준 레포/브랜치를 고르는 계약."""

    def infer_repository_refs(
        self,
        user_input: str,
        runs: list[Any],
        messages: list[ChatMessage],
    ) -> RepositoryTargetPlanResult: ...


class IntentResolveResult(Protocol):
    """LLM intent resolver가 고른 질문 종류와 기준 변경 모드를 돌려주는 계약."""

    intent: str
    basis_mode: str | None
    reason: str | None


class IntentResolver(Protocol):
    """정해진 키워드로 못 잡은 자연어 질문의 의도를 고르는 계약."""

    def resolve_intent(
        self,
        user_input: str,
        messages: list[ChatMessage],
    ) -> IntentResolveResult: ...


class PathTargetPlanResult(Protocol):
    """LLM이 사용자 표현을 실제 SQL path prefix 후보 중 하나로 고른 결과."""

    selected_path: str | None
    reason: str | None


class PathTargetResolver(Protocol):
    """오타가 섞인 폴더 표현을 실제 저장된 path prefix에 맞추는 계약."""

    def resolve_path_target(
        self,
        user_input: str,
        path_candidates: list[str],
        messages: list[ChatMessage],
    ) -> PathTargetPlanResult: ...


class AgentChatUseCase(Protocol):
    """HTTP 라우터가 내부 저장소나 에이전트 구현을 몰라도 쓰는 채팅 유스케이스."""

    def create_session(
        self,
        request: ChatSessionCreateRequestDTO,
    ) -> ChatSessionDetailResponseDTO: ...

    def get_session_detail(self, session_id: str) -> ChatSessionDetailResponseDTO: ...

    def send_message(
        self,
        db: Session,
        session_id: str,
        request: ChatSendMessageRequestDTO,
    ) -> ChatSendMessageResponseDTO: ...
