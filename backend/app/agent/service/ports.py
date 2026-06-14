from typing import Protocol

from app.agent.api.schema import (
    ChatSessionCreateRequestDTO,
    ChatSessionDetailResponseDTO,
    ChatSendMessageRequestDTO,
    ChatSendMessageResponseDTO,
)
from app.agent.domain.chat import ChatMessage, ChatSession, ChatTurn


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
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> str: ...


class AgentChatUseCase(Protocol):
    """HTTP 라우터가 내부 저장소나 에이전트 구현을 몰라도 쓰는 채팅 유스케이스."""

    def create_session(
        self,
        request: ChatSessionCreateRequestDTO,
    ) -> ChatSessionDetailResponseDTO: ...

    def get_session_detail(self, session_id: str) -> ChatSessionDetailResponseDTO: ...

    def send_message(
        self,
        session_id: str,
        request: ChatSendMessageRequestDTO,
    ) -> ChatSendMessageResponseDTO: ...
