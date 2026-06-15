from dataclasses import dataclass, field
from datetime import datetime

from app.pipeline.api.schemas import RetrievalChunk
from app.repo_rag.api.schemas import (
    RepoRagSyncRequest,
    SyncEventView,
    SyncJobStatus,
    SyncJobView,
    SyncTriggerType,
)
from app.repo_rag.domain.identity import utcnow


@dataclass(slots=True)
class EmbeddedChunk:
    """청크와 그 임베딩 벡터를 함께 담는 값 객체.

    임베딩 생성 책임은 IndexingService가 갖고, 저장소(store)는 이미 임베딩이
    부착된 청크만 영속화한다. embedding이 None이면 저장소는 벡터를 비워 둔다.
    """

    chunk: RetrievalChunk
    embedding: list[float] | None = None


@dataclass(slots=True)
class RepositoryRecord:
    id: str
    source_key: str
    name: str
    branch: str
    repository_url: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class SnapshotRecord:
    id: str
    repository_id: str
    branch: str
    commit_sha: str
    file_count: int
    created_at: datetime


@dataclass(slots=True)
class FileRecord:
    id: str
    repository_id: str
    snapshot_id: str
    path: str
    content_hash: str
    status: str
    is_active: bool
    last_seen_at: datetime
    deleted_at: datetime | None = None


@dataclass(slots=True)
class ChunkRecord:
    id: str
    repository_id: str
    file_id: str
    snapshot_id: str
    source_path: str
    chunk_hash: str
    text: str
    citation: str
    is_active: bool
    created_at: datetime
    deleted_at: datetime | None = None
    chunk_type: str | None = None
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    language: str | None = None

    def to_chunk(self) -> RetrievalChunk:
        return RetrievalChunk(
            id=self.id,
            source_path=self.source_path,
            text=self.text,
            citation=self.citation,
            chunk_type=self.chunk_type,
            symbol_name=self.symbol_name,
            start_line=self.start_line,
            end_line=self.end_line,
            language=self.language,
        )


@dataclass(slots=True)
class SyncJobRecord:
    id: str
    trigger_type: SyncTriggerType
    branch: str
    idempotency_key: str
    lock_key: str
    request: RepoRagSyncRequest = field(repr=False)
    repository_id: str | None = None
    requested_commit_sha: str | None = None
    status: SyncJobStatus = "queued"
    error: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def to_view(self) -> SyncJobView:
        return SyncJobView(
            id=self.id,
            repository_id=self.repository_id,
            trigger_type=self.trigger_type,
            branch=self.branch,
            requested_commit_sha=self.requested_commit_sha,
            idempotency_key=self.idempotency_key,
            status=self.status,
            error=self.error,
            created_at=self.created_at,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )


@dataclass(slots=True)
class SyncEventRecord:
    id: str
    job_id: str
    stage: str
    detail: str
    created_at: datetime

    def to_view(self) -> SyncEventView:
        return SyncEventView(
            id=self.id,
            job_id=self.job_id,
            stage=self.stage,
            detail=self.detail,
            created_at=self.created_at,
        )
