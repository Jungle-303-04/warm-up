from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.pipeline import PipelineRequest, RepoSnapshot, RetrievalChunk


SyncTriggerType = Literal["manual", "schedule", "webhook"]
SyncJobStatus = Literal["queued", "running", "succeeded", "failed"]
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
