from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin


class RagIndexRun(Base, IdMixin):
    __tablename__ = "rag_index_run"

    repository_full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    branch: Mapped[str | None] = mapped_column(String, nullable=True)
    commit_sha: Mapped[str] = mapped_column(String, nullable=False, index=True)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    total_files: Mapped[int] = mapped_column(Integer, nullable=False)
    indexed_files: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped_files: Mapped[int] = mapped_column(Integer, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False)


class RagFileSnapshot(Base, IdMixin):
    __tablename__ = "rag_file_snapshot"

    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag_index_run.id"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    sha: Mapped[str | None] = mapped_column(String, nullable=True)
    commit_sha: Mapped[str] = mapped_column(String, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    citation: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    html_url: Mapped[str | None] = mapped_column(String, nullable=True)


class RagChunk(Base, IdMixin):
    __tablename__ = "rag_chunk"

    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag_index_run.id"),
        nullable=False,
        index=True,
    )
    file_snapshot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag_file_snapshot.id"),
        nullable=False,
        index=True,
    )
    external_chunk_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chunk_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    commit_sha: Mapped[str] = mapped_column(String, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    symbol_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    citation: Mapped[str] = mapped_column(String, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    direct_implementation_evidence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )


class RagSkippedFile(Base, IdMixin):
    __tablename__ = "rag_skipped_file"

    run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag_index_run.id"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
