from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BlockType

if TYPE_CHECKING:
    # 실행 중 import가 아니라 타입 검사기/IDE 자동완성용 import다.
    from app.models.page import Page


# Page 안에 들어가는 개별 블록을 표현하는 모델이다.
class PageBlock(Base):
    __tablename__ = "page_blocks"

    # 같은 Page 안에서는 order_index가 중복되지 않도록 막는다.
    __table_args__ = (
        UniqueConstraint(
            "page_id",
            "order_index",
            name="uq_page_block_order",
        ),
    )

    # 블록의 고유 번호다.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 이 블록이 어느 Page에 속하는지 저장하는 실제 DB 컬럼이다.
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 문단, 제목, 체크리스트 같은 블록 종류를 저장한다.
    type: Mapped[BlockType] = mapped_column(
        Enum(BlockType, name="block_type"),
        nullable=False,
    )

    # 블록에 표시될 텍스트 내용이다.
    content: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # 체크리스트 블록일 때 체크 여부를 저장한다. 다른 블록은 None일 수 있다.
    checked: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # 한 페이지 안에서 블록이 보이는 순서를 저장한다.
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # DB 서버 시간을 기준으로 블록 생성 시각이 자동 저장된다.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 블록이 수정될 때마다 DB 서버 시간으로 갱신된다.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    #다른 테이블 객체 가져오고 싶으면
    # page_id를 이용해 연결된 Page 객체를 block.page로 꺼내 쓸 수 있게 한다.
    page: Mapped["Page"] = relationship(
        back_populates="blocks", #반대 테이블에는 나를 가리키는 이름이 blocks이다
    )
