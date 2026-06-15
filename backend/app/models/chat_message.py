from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession


class ChatMessage(Base):
    # AI 채팅방 안에 들어가는 개별 메시지를 저장하는 테이블.
    # 사용자 질문, AI 답변이 각각 한 row로 저장된다.
    __tablename__ = "chat_messages"

    # 메시지 고유 ID.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # 이 메시지가 속한 채팅방 ID.
    # chat_sessions.id와 연결되며, 채팅방이 삭제되면 메시지도 같이 삭제된다.
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 메시지를 보낸 주체.
    # 예: "user"는 사용자 질문, "assistant"는 AI 답변.
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # 메시지 본문.
    # 사용자 질문이나 AI가 생성한 답변 텍스트가 저장된다.
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # AI 답변을 만들 때 참고한 RAG 검색 결과.
    # 일반 사용자 메시지에는 비어 있을 수 있다.
    references: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # 메시지가 생성된 시간.
    # DB가 현재 시간을 자동으로 넣어준다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 이 메시지가 속한 ChatSession 객체.
    # ChatSession.messages와 서로 연결된다.
    session: Mapped["ChatSession"] = relationship(
        back_populates="messages",
    )
