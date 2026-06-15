from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.user import User


class ChatSession(Base):
    # AI 채팅방 목록을 저장하는 테이블.
    # 채팅 메시지 자체는 chat_messages 테이블에 저장되고,
    # 이 테이블은 "대화방 하나"의 정보를 담당한다.
    __tablename__ = "chat_sessions"

    # 채팅방 고유 ID.
    # chat_messages.session_id가 이 값을 참조한다.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # 이 채팅방을 소유한 사용자 ID.
    # users.id와 연결되며, 사용자가 삭제되면 해당 사용자의 채팅방도 같이 삭제된다.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 채팅방 제목.
    # 처음 생성할 때 제목을 따로 지정하지 않으면 기본값으로 저장된다.
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="새 AI 대화",
    )

    # 채팅방이 처음 생성된 시간.
    # DB가 현재 시간을 자동으로 넣어준다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 채팅방이 마지막으로 수정된 시간.
    # SQLAlchemy에서 update가 발생하면 현재 시간으로 갱신된다.
    updated_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 이 채팅방에 속한 메시지 목록.
    # ChatMessage.session과 서로 연결되며,
    # 채팅방이 삭제되면 딸린 메시지도 같이 삭제된다.
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
