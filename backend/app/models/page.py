from __future__ import annotations

from datetime import date as DateType
from datetime import datetime as DateTimeType
from datetime import time as TimeType
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, JSON, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.association import page_tags
from app.models.enums import PageType

if TYPE_CHECKING:
    # 타입 힌트용 import다. 실행 중 순환 import를 피하려고 TYPE_CHECKING 안에서만 가져온다.
    from app.models.comment import Comment
    from app.models.page_block import PageBlock
    from app.models.tag import Tag
    from app.models.user import User

class Page(Base):
    # 캘린더에 표시되는 회의록/회고 같은 페이지 정보를 저장하는 테이블이다.
    __tablename__ = "pages"

    # 페이지 한 개를 구분하는 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 페이지 종류다. PageType enum에 정의된 값만 저장할 수 있다.
    type : Mapped[PageType] = mapped_column(
        Enum(PageType, name="page_type"),
        nullable=False,
        # 회의록만 보기, 회고만 보기처럼 타입별 조회가 많아서 인덱스를 둔다.
        index=True,
    )

    # 페이지 제목이다. 화면 목록과 상세 페이지에서 주로 보여준다.
    title : Mapped[str] = mapped_column(
        String(200),
        nullable = False,
    )

    # 페이지가 속한 날짜다. 캘린더 조회의 기준이 된다.
    date: Mapped[DateType] = mapped_column(
        Date,
        nullable=False,
        # 날짜별 페이지 조회가 많아서 인덱스를 둔다.
        index=True,
    )

    # 회의나 일정처럼 시작 시간이 있는 페이지를 위해 둔다. 메모/회고는 비어 있을 수 있다.
    start_time : Mapped[TimeType | None] = mapped_column(
        Time,
        nullable = True,
    )

    # 회의나 일정의 종료 시간이다. 시간이 필요 없는 페이지는 비어 있을 수 있다.
    end_time : Mapped[TimeType | None] = mapped_column(
        Time,
        nullable = True,
    )

    # 이 페이지를 작성한 사용자의 id다. 실제 DB에는 User 객체가 아니라 이 숫자가 저장된다.
    author_id : Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), #users 테이블의 id중 하나여야 한다
        nullable = False,
        # 사용자별 작성 페이지 목록을 빠르게 찾기 위해 인덱스를 둔다.
        index = True,
    )

    # 참석자 이름 목록이다. 지금은 별도 테이블 없이 JSON 배열로 간단히 저장한다.
    participants: Mapped[list[str]] = mapped_column(
        JSON,
        default = list,
        nullable = False,
    )

    # AI가 만든 요약문이다. 아직 요약이 없을 수 있으므로 None을 허용한다.
    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 페이지가 처음 생성된 시각이다. DB 서버 시간이 자동으로 들어간다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 페이지가 마지막으로 수정된 시각이다. 수정될 때 자동으로 갱신된다.
    updated_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    #SQLAlchemy가 author_id를 보고 연결해준다 ex) page.author.nickname
    # author_id를 보고 연결된 User 객체를 바로 사용할 수 있게 한다. 예: page.author.nickname
    author: Mapped["User"] = relationship(
        back_populates="pages",
    )

    #page.blocks 가능
    # 페이지 본문 블록 목록이다. order_index 순서대로 정렬되어 나온다.
    blocks: Mapped[list["PageBlock"]] = relationship(
        back_populates="page",
        # 페이지가 삭제되면 그 안의 블록도 같이 삭제한다.
        cascade="all, delete-orphan",
        order_by="PageBlock.order_index",
    )

    #page.comment 가능
    # 페이지에 달린 댓글 목록이다. 실제 사용은 page.comments다.
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan", #페이지가 삭제되면 같이 삭제됨
    )

    #page.tag 가능
    # 페이지에 붙은 태그 목록이다. page_tags 중간 테이블을 통해 Tag와 연결된다.
    tags: Mapped[list["Tag"]] = relationship(
        secondary=page_tags,
        back_populates="pages",
    )

