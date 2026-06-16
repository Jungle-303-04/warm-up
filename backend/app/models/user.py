from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    # 실행 중 import가 아니라 타입 검사기/IDE 자동완성용 import다.
    from app.models.comment import Comment
    from app.models.daily_message import DailyMessage
    from app.models.page import Page


# 서비스를 사용하는 회원을 표현하는 모델이다.
class User(Base):
    __tablename__ = "users"

    # 사용자의 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 로그인에 쓰는 이메일이다. 중복 가입을 막기 위해 unique=True다.
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # 원본 비밀번호가 아니라 해시된 비밀번호를 저장한다.
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # 화면에 표시할 사용자 이름이다.
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # DB 서버 시간을 기준으로 가입 시각이 자동 저장된다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 이 사용자가 작성한 Page들을 user.pages 리스트로 꺼내 쓸 수 있게 한다.
    pages: Mapped[list["Page"]] = relationship(
        back_populates="author",
        # User에서 빠진 페이지는 고아 데이터로 보고 같이 삭제한다.
        cascade="all, delete-orphan",
    )

    daily_messages: Mapped[list["DailyMessage"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

    # 이 사용자가 작성한 Comment들을 user.comments 리스트로 꺼내 쓸 수 있게 한다.
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        # User에서 빠진 댓글은 고아 데이터로 보고 같이 삭제한다.
        cascade="all, delete-orphan",
    )
