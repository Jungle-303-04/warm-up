from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BlockType

if TYPE_CHECKING:
    from app.models.page import Page


class PageBlock(Base):
    __tablename__ = "page_blocks"

    __table_args__ = (
        UniqueConstraint(
            "page_id",
            "order_index",
            name="uq_page_block_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[BlockType] = mapped_column(
        Enum(BlockType, name="block_type"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    checked: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    page: Mapped["Page"] = relationship(
        back_populates="blocks",
    )