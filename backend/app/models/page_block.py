from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BlockType

if TYPE_CHECKING:
    # 타입 힌트용 import다. 실행 중 순환 import를 피하려고 TYPE_CHECKING 안에서만 가져온다.
    from app.models.page import Page


class PageBlock(Base):
    # 페이지 본문을 구성하는 블록들을 저장하는 테이블이다.
    __tablename__ = "page_blocks"

    #order_index 안겹치게
    # 같은 페이지 안에서 order_index가 중복되지 않도록 막는다.
    __table_args__ = (
        UniqueConstraint(
            "page_id",
            "order_index",
            name="uq_page_block_order",
        ),
    )

    # 블록 한 개를 구분하는 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이 블록이 어느 페이지에 속하는지 저장한다.
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), #페이지가 삭제되면 이 블록도 삭제
        nullable=False,
        # 특정 페이지의 블록 목록을 자주 조회하므로 인덱스를 둔다.
        index=True,
    )

    #문단이냐 제목이냐 체크리스트냐
    # 블록이 문단/제목/불릿/체크리스트/코드 중 어떤 종류인지 저장한다.
    type: Mapped[BlockType] = mapped_column(
        Enum(BlockType, name="block_type"),
        nullable=False,
    )

    # 내용
    # 블록의 실제 내용이다. 긴 글이나 코드도 담을 수 있게 Text를 사용한다.
    content: Mapped[str] = mapped_column(
        Text, #길어질 수 있으므로
        default="",
        nullable=False,
    )

    #체크 리스트
    # 체크리스트 블록일 때 체크 여부를 저장한다. 체크리스트가 아니면 None일 수 있다.
    checked: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    #블록 순서
    # 페이지 안에서 블록이 몇 번째로 보일지 정하는 순서값이다.
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    #언제 만들어졌냐
    # 블록이 처음 만들어진 시각이다.
    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    #언제 수정되었냐
    # 블록이 마지막으로 수정된 시각이다. 수정될 때 자동 갱신된다.
    updated_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    #page_id와 연결된 실제 page 객체를 바로 쓸 수 있다
    # page_id를 보고 연결된 Page 객체를 바로 사용할 수 있게 한다. 예: block.page.title
    page: Mapped["Page"] = relationship(
        back_populates="blocks",
    )
