from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


# "오늘의 한마디" 글 하나를 DB에 저장하기 위한 SQLAlchemy 모델이다.
# 실제 DB에서는 daily_messages 테이블로 만들어진다.
class DailyMessage(Base):
    __tablename__ = "daily_messages"

    # 한마디 글의 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이 한마디를 작성한 사용자의 id다.
    # users.id를 참조하므로 어떤 사용자가 쓴 글인지 알 수 있다.
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 사용자가 입력한 한마디 본문이다.
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 글이 처음 생성된 시각이다. DB 서버 시간이 자동으로 들어간다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 글이 수정된 시각이다. 수정될 때마다 DB 서버 시간이 갱신된다.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # author_id로 연결된 User 객체를 message.author로 꺼내 쓸 수 있게 한다.
    author: Mapped["User"] = relationship(
        back_populates="daily_messages",
    )
