from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agent.api.schema import (
    ChatSendMessageRequestDTO,
    ChatSendMessageResponseDTO,
    ChatSessionCreateRequestDTO,
    ChatSessionDetailResponseDTO,
)
from app.agent.service.ports import AgentChatUseCase
from app.container import AppContainer
from app.db.session import get_session

agent = APIRouter(prefix="/agent")


@agent.post(
    "/chat/sessions",
    tags=["agent"],
    response_model=ChatSessionDetailResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
@inject
def create_chat_session(
    request: ChatSessionCreateRequestDTO,
    chat_service: AgentChatUseCase = Depends(Provide[AppContainer.agent_chat_service]),
) -> ChatSessionDetailResponseDTO:
    """프론트가 메시지를 보내기 전에 채팅방과 message history 공간을 만들게 한다."""

    return chat_service.create_session(request)


@agent.get(
    "/chat/sessions/{session_id}",
    tags=["agent"],
    response_model=ChatSessionDetailResponseDTO,
)
@inject
def get_chat_session(
    session_id: str,
    chat_service: AgentChatUseCase = Depends(Provide[AppContainer.agent_chat_service]),
) -> ChatSessionDetailResponseDTO:
    """새로고침이나 채팅방 재진입 시 현재까지의 메시지 목록을 복원한다."""

    try:
        return chat_service.get_session_detail(session_id)
    except ValueError as exc:
        raise_chat_not_found(exc)


@agent.post(
    "/chat/sessions/{session_id}/messages",
    tags=["agent"],
    response_model=ChatSendMessageResponseDTO,
)
@inject
def send_chat_message(
    session_id: str,
    request: ChatSendMessageRequestDTO,
    db: Session = Depends(get_session),
    chat_service: AgentChatUseCase = Depends(Provide[AppContainer.agent_chat_service]),
) -> ChatSendMessageResponseDTO:
    """사용자 입력 하나를 agent turn으로 처리하고 갱신된 메시지 목록을 반환한다."""

    try:
        return chat_service.send_message(db, session_id, request)
    except ValueError as exc:
        raise_chat_not_found(exc)


def raise_chat_not_found(exc: ValueError) -> None:
    """서비스의 세션 없음 오류를 HTTP 404 응답으로 바꾼다."""

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    ) from exc
