"""노트북 Postgres ORM 모델.

sqlalchemy에 의존하므로 Postgres 경로에서만 import 한다.
repo_snapshot([{path, content} ...])은 JSONB로 저장한다.
notebook_sources는 notebook_id FK(ON DELETE CASCADE)로 노트북에 종속된다.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Computed, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings

EMBEDDING_DIMENSION = get_settings().embedding_dimension
SEARCH_TEXT_CONFIG = get_settings().search_text_config


class Base(DeclarativeBase):
    pass


class NotebookModel(Base):
    __tablename__ = "notebooks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceModel(Base):
    __tablename__ = "notebook_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    branch: Mapped[str | None] = mapped_column(String, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    derived_from_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True)
    lineage_source_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    repo_commits: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    repo_snapshot: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatMessageModel(Base):
    __tablename__ = "notebook_chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    source_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotebookChunkModel(Base):
    __tablename__ = "notebook_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebook_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    format: Mapped[str | None] = mapped_column(String, nullable=True)
    heading_path: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_chunk_id: Mapped[str | None] = mapped_column(String, nullable=True)
    prev_chunk_id: Mapped[str | None] = mapped_column(String, nullable=True)
    next_chunk_id: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION), nullable=True
    )
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(f"to_tsvector('{SEARCH_TEXT_CONFIG}', text)", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NotebookIndexProgressModel(Base):
    __tablename__ = "notebook_index_progress"

    source_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebook_sources.id", ondelete="CASCADE"),
        primary_key=True,
    )
    notebook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ArtifactModel(Base):
    """산출물(다이어그램/요약/메모) ORM 모델.

    source_ids는 생성 기준 소스 id 배열(note는 빈 배열). JSONB로 저장한다.
    notebook_id FK(ON DELETE CASCADE)로 노트북에 종속된다.
    """

    __tablename__ = "notebook_artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
