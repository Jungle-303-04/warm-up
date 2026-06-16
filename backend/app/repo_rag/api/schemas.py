from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from app.pipeline.api.schemas import (
    DEFAULT_BRANCH,
    DEFAULT_REPO,
    PipelineRequest,
    RepoSnapshot,
    RetrievalChunk,
)

SyncTriggerType = Literal["manual", "schedule", "webhook"]
SyncJobStatus = Literal[
    "queued",
    "running",
    "running_sync",
    "running_code_index",
    "running_rag_index",
    "running_agent_proposal",
    "succeeded",
    "failed",
]
RepoFileChangeStatus = Literal["added", "modified", "deleted", "unchanged"]


class RepoRagSyncRequest(PipelineRequest):
    trigger_type: SyncTriggerType = "manual"
    requested_commit_sha: str | None = None


class RepoFileChange(BaseModel):
    path: str
    status: RepoFileChangeStatus
    previous_hash: str | None = None
    current_hash: str | None = None


class SyncJobView(BaseModel):
    id: str
    repository_id: str | None = None
    trigger_type: SyncTriggerType
    branch: str
    requested_commit_sha: str | None = None
    idempotency_key: str
    status: SyncJobStatus
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SyncEventView(BaseModel):
    id: str
    job_id: str
    stage: str
    detail: str
    created_at: datetime


class RepoRagSyncResponse(BaseModel):
    job: SyncJobView
    repository: RepoSnapshot
    changes: list[RepoFileChange]
    active_chunks: list[RetrievalChunk]
    events: list[SyncEventView]


class SyncJobAcceptedResponse(BaseModel):
    """Postgres 경로: sync를 큐에 넣고 즉시 반환하는 응답(202)."""

    job: SyncJobView


class SyncJobDetailResponse(BaseModel):
    """job 상태 조회 응답."""

    job: SyncJobView
    events: list[SyncEventView]


class RepoRagSearchRequest(BaseModel):
    query: str
    repository: str = DEFAULT_REPO
    branch: str = DEFAULT_BRANCH
    repository_url: str | None = None
    limit: int = 10

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query는 비어 있을 수 없습니다")
        return query

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int) -> int:
        if value < 1:
            raise ValueError("limit은 1 이상이어야 합니다")
        return value


class RepoRagSearchHit(BaseModel):
    chunk: RetrievalChunk
    score: float
    vector_score: float
    keyword_score: float


class RepoRagSearchResponse(BaseModel):
    query: str
    hits: list[RepoRagSearchHit]
