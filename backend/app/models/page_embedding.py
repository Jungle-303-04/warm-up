from __future__ import annotations

from datetime import datetime as DateTimeType
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.page import Page


class PageEmbedding(Base):
    __tablename__ = "page_embeddings"

#     page_embeddings
# id | page_id | chunk_index | chunk_text      | embedding
# 1  | 1       | 0           | 회의 안건...     | [0.12, -0.03, ...]
# 2  | 1       | 1           | 결정 사항...     | [0.04,  0.22, ...]
# 3  | 1       | 2           | TODO...          | [-0.11, 0.08, ...]


    #이건 같은 게시글 안에서 chunk_index가 중복되지 않게 막는 제약조건이다.
    __table_args__ = (
        UniqueConstraint(
            "page_id",
            "chunk_index",
            name="uq_page_embeddings_page_id_chunk_index",
        ),
    )

    #row 번호
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    #이 chunk가 어느 회의/회고에서 나왔는지
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    #한 회의/회고 안에서 몇번째 chunk인지
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    #1536 차원 vector
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(1536),
        nullable=False,
    )

    created_at: Mapped[DateTimeType] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    page: Mapped["Page"] = relationship()