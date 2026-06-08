from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, JSON, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.association import page_tags
from app.models.enums import PageType

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.page_block import PageBlock
    from app.models.tag import Tag
    from app.models.user import User


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    type: Mapped[PageType] = mapped_column(
        Enum(PageType, name="page_type"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    participants: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    author: Mapped["User"] = relationship(
        back_populates="pages",
    )

    blocks: Mapped[list["PageBlock"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="PageBlock.order_index",
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary=page_tags,
        back_populates="pages",
    )