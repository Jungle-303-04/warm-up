from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, JSON, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PageType

if TYPE_CHECKING:
    # 실행 중 import가 아니라 타입 검사기/IDE 자동완성용 import다.
    from app.models.comment import Comment
    from app.models.page_block import PageBlock
    from app.models.user import User


# 회의록/회고 같은 하나의 페이지 문서를 표현하는 모델이다.
class Page(Base):
    __tablename__ = "pages"

    # 페이지의 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 페이지 종류를 MEETING, RETROSPECTIVE 중 하나로 저장한다.
    type: Mapped[PageType] = mapped_column(
        Enum(PageType, name="page_type"),
        nullable=False,
        index=True,
    )

    # 페이지 제목이다.
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # 캘린더에서 기준이 되는 페이지 날짜다.
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # 일정 시작 시간이 없을 수도 있어서 nullable=True다.
    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    # 일정 종료 시간이 없을 수도 있어서 nullable=True다.
    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    # 작성자 User의 id를 저장하는 실제 DB 컬럼이다.
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 참여자 이름 목록을 JSON 배열 형태로 저장한다.
    participants: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # AI가 만든 요약이 아직 없을 수 있어서 nullable=True다.
    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # DB 서버 시간을 기준으로 페이지 생성 시각이 자동 저장된다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 페이지가 수정될 때마다 DB 서버 시간으로 갱신된다.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # author_id를 이용해 연결된 User 객체를 page.author로 꺼내 쓸 수 있게 한다.
    author: Mapped["User"] = relationship(
        back_populates="pages",
    )

    # 이 페이지에 속한 블록들을 page.blocks 리스트로 꺼내 쓸 수 있게 한다.
    blocks: Mapped[list["PageBlock"]] = relationship(
        back_populates="page",
        # Page에서 빠진 블록은 고아 데이터로 보고 같이 삭제한다.
        cascade="all, delete-orphan",
        # 블록은 order_index 순서대로 정렬해서 가져온다.
        order_by="PageBlock.order_index",
    )

    # 이 페이지에 달린 댓글들을 page.comments 리스트로 꺼내 쓸 수 있게 한다.
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="page",
        # Page에서 빠진 댓글은 고아 데이터로 보고 같이 삭제한다.
        cascade="all, delete-orphan",
    )
