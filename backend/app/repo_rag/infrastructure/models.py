"""repo-rag Postgres ORM 모델.

테이블 이름은 16-repo-rag-implementation-plan.md의 계획을 따른다.
이 모듈은 sqlalchemy/pgvector에 의존하므로 Postgres 경로에서만 import 한다.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.repo_rag.infrastructure.db import Base, TimestampMixin

EMBEDDING_DIMENSION = get_settings().embedding_dimension
SEARCH_TEXT_CONFIG = get_settings().search_text_config


def active_filters(model: type) -> tuple:
    """active row 조건(is_active=True, 미삭제)의 단일 출처.

    여러 쿼리에서 `*active_filters(ChunkModel)`처럼 풀어 쓴다.
    """
    return (model.is_active.is_(True), model.deleted_at.is_(None))


class RepositoryModel(Base):
    __tablename__ = "repository_connections"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    branch: Mapped[str] = mapped_column(String, nullable=False)
    repository_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SnapshotModel(Base):
    __tablename__ = "branch_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repository_connections.id"), index=True, nullable=False
    )
    branch: Mapped[str] = mapped_column(String, nullable=False)
    commit_sha: Mapped[str] = mapped_column(String, nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FileModel(Base):
    __tablename__ = "source_files"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repository_connections.id"), index=True, nullable=False
    )
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("branch_snapshots.id"), nullable=False)
    path: Mapped[str] = mapped_column(String, index=True, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChunkModel(Base):
    __tablename__ = "source_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository_id: Mapped[str] = mapped_column(
        ForeignKey("repository_connections.id"), index=True, nullable=False
    )
    file_id: Mapped[str] = mapped_column(ForeignKey("source_files.id"), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("branch_snapshots.id"), nullable=False)
    source_path: Mapped[str] = mapped_column(String, index=True, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[str] = mapped_column(String, nullable=False)
    chunk_type: Mapped[str | None] = mapped_column(String, nullable=True)
    symbol_name: Mapped[str | None] = mapped_column(String, nullable=True)
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION), nullable=True
    )
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(f"to_tsvector('{SEARCH_TEXT_CONFIG}', text)", persisted=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# 특수 인덱스 정의 (GIN, HNSW)
Index(
    "ix_source_chunks_content_tsv",
    ChunkModel.content_tsv,
    postgresql_using="gin",
)

Index(
    "ix_source_chunks_embedding_hnsw",
    ChunkModel.embedding,
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"},
)

Index(
    "ix_source_chunks_active",
    ChunkModel.repository_id,
    postgresql_where=ChunkModel.is_active.is_(True),
)


class JobModel(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    branch: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, index=True, nullable=False)
    lock_key: Mapped[str] = mapped_column(String, index=True, nullable=False)
    repository_id: Mapped[str | None] = mapped_column(String, nullable=True)
    requested_commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="queued", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventModel(Base, TimestampMixin):
    __tablename__ = "sync_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("sync_jobs.id"), index=True, nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
