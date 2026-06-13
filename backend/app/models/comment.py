from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    # 실행 중 import가 아니라 타입 검사기/IDE 자동완성용 import다.
    from app.models.page import Page
    from app.models.user import User


# 댓글 테이블을 표현하는 SQLAlchemy 모델이다.
class Comment(Base):
    __tablename__ = "comments"

    # 댓글의 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이 댓글이 어느 Page에 달렸는지 저장하는 실제 DB 컬럼이다.
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 이 댓글을 작성한 User의 id를 저장하는 실제 DB 컬럼이다.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 댓글 본문이다.
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # DB 서버 시간을 기준으로 댓글 생성 시각이 자동 저장된다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # page_id를 이용해 연결된 Page 객체를 comment.page로 꺼내 쓸 수 있게 한다.
    page: Mapped["Page"] = relationship(
        back_populates="comments",
    )

    # user_id를 이용해 연결된 User 객체를 comment.author로 꺼내 쓸 수 있게 한다.
    author: Mapped["User"] = relationship(
        back_populates="comments",
    )
