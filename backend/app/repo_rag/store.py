from datetime import datetime
from typing import Protocol

from app.pipeline.schemas import RepoSnapshot, RetrievalChunk
from app.repo_rag.records import (
    ChunkRecord,
    FileRecord,
    RepositoryRecord,
    SnapshotRecord,
    SyncEventRecord,
    SyncJobRecord,
)
from app.repo_rag.schemas import RepoFileChange, RepoRagSyncRequest


class RepoRagStore(Protocol):
    def create_job(self, request: RepoRagSyncRequest) -> SyncJobRecord: ...

    def get_job(self, job_id: str) -> SyncJobRecord: ...

    def start_job(self, job_id: str) -> SyncJobRecord: ...

    def claim_job_lock(self, job_id: str) -> None: ...

    def release_job_lock(self, job_id: str) -> None: ...

    def attach_job_repository(self, job_id: str, repository_id: str) -> None: ...

    def finish_job(self, job_id: str) -> SyncJobRecord: ...

    def fail_job(self, job_id: str, error: str) -> SyncJobRecord: ...

    def record_event(self, job_id: str, stage: str, detail: str) -> SyncEventRecord: ...

    def job_events(self, job_id: str) -> list[SyncEventRecord]: ...

    def upsert_repository(
        self,
        request: RepoRagSyncRequest,
        snapshot: RepoSnapshot,
    ) -> RepositoryRecord: ...

    def active_files(self, repository_id: str) -> dict[str, FileRecord]: ...

    def record_snapshot(
        self,
        repository_id: str,
        snapshot: RepoSnapshot,
    ) -> SnapshotRecord: ...

    def apply_file_changes(
        self,
        repository_id: str,
        snapshot_id: str,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> dict[str, FileRecord]: ...

    def upsert_chunks(
        self,
        repository_id: str,
        snapshot_id: str,
        file_records: dict[str, FileRecord],
        chunks: list[RetrievalChunk],
    ) -> list[ChunkRecord]: ...

    def active_chunks(self, repository_id: str) -> list[RetrievalChunk]: ...

    def hard_delete_inactive(self, batch_size: int, cutoff: datetime) -> int: ...
