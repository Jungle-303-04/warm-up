from datetime import datetime

from app.pipeline.api.schemas import RepoSnapshot, RetrievalChunk
from app.repo_rag.api.schemas import RepoFileChange, RepoRagSyncRequest, SyncJobStatus
from app.repo_rag.domain.identity import (
    file_hash,
    hash_text,
    idempotency_key,
    lock_key,
    new_id,
    source_key,
    utcnow,
)
from app.repo_rag.domain.records import (
    ChunkRecord,
    EmbeddedChunk,
    FileRecord,
    RepositoryRecord,
    SnapshotRecord,
    SyncEventRecord,
    SyncJobRecord,
)

ACTIVE_JOB_STATUSES: set[SyncJobStatus] = {"queued", "running"}


class InMemoryRepoRagStore:
    def __init__(self) -> None:
        self.repositories: dict[str, RepositoryRecord] = {}
        self.repository_ids_by_key: dict[str, str] = {}
        self.snapshots: dict[str, SnapshotRecord] = {}
        self.files: dict[str, FileRecord] = {}
        self.active_file_ids_by_path: dict[tuple[str, str], str] = {}
        self.chunks: dict[str, ChunkRecord] = {}
        self.jobs: dict[str, SyncJobRecord] = {}
        self.active_job_ids_by_key: dict[str, str] = {}
        self.active_job_ids_by_lock_key: dict[str, str] = {}
        self.running_job_ids_by_lock_key: dict[str, str] = {}
        self.events: dict[str, list[SyncEventRecord]] = {}

    def create_job(self, request: RepoRagSyncRequest) -> SyncJobRecord:
        request_idempotency_key = idempotency_key(request)
        active_job_id = self.active_job_ids_by_key.get(request_idempotency_key)
        if active_job_id:
            active_job = self.jobs[active_job_id]
            if active_job.status in ACTIVE_JOB_STATUSES:
                return active_job

        request_lock_key = lock_key(request)
        active_job_id = self.active_job_ids_by_lock_key.get(request_lock_key)
        if active_job_id:
            active_job = self.jobs[active_job_id]
            if active_job.status in ACTIVE_JOB_STATUSES:
                return active_job

        job = SyncJobRecord(
            id=new_id(),
            trigger_type=request.trigger_type,
            branch=request.branch,
            requested_commit_sha=request.requested_commit_sha,
            idempotency_key=request_idempotency_key,
            lock_key=request_lock_key,
            request=request,
        )
        self.jobs[job.id] = job
        self.active_job_ids_by_key[request_idempotency_key] = job.id
        self.active_job_ids_by_lock_key[request_lock_key] = job.id
        self.record_event(job.id, "job_queued", f"{request.trigger_type} sync job queued")
        return job

    def claim_next_queued_job(self) -> SyncJobRecord | None:
        queued = [job for job in self.jobs.values() if job.status == "queued"]
        if not queued:
            return None
        job = min(queued, key=lambda job: job.created_at)
        job.status = "running"
        self.record_event(job.id, "job_claimed", "claimed by worker")
        return job

    def get_job(self, job_id: str) -> SyncJobRecord:
        return self.jobs[job_id]

    def start_job(self, job_id: str) -> SyncJobRecord:
        job = self.get_job(job_id)
        job.status = "running"
        job.started_at = job.started_at or utcnow()
        self.record_event(job.id, "job_started", "sync worker started")
        return job

    def claim_job_lock(self, job_id: str) -> None:
        job = self.get_job(job_id)
        running_job_id = self.running_job_ids_by_lock_key.get(job.lock_key)
        if running_job_id and running_job_id != job.id:
            raise ValueError(f"sync already running for {job.lock_key}")

        self.running_job_ids_by_lock_key[job.lock_key] = job.id
        self.record_event(job.id, "lock_acquired", job.lock_key)

    def release_job_lock(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if self.running_job_ids_by_lock_key.get(job.lock_key) == job.id:
            self.running_job_ids_by_lock_key.pop(job.lock_key, None)

    def attach_job_repository(self, job_id: str, repository_id: str) -> None:
        self.get_job(job_id).repository_id = repository_id

    def finish_job(self, job_id: str) -> SyncJobRecord:
        job = self.get_job(job_id)
        job.status = "succeeded"
        job.finished_at = utcnow()
        self.active_job_ids_by_key.pop(job.idempotency_key, None)
        self.active_job_ids_by_lock_key.pop(job.lock_key, None)
        self.release_job_lock(job.id)
        self.record_event(job.id, "job_succeeded", "sync worker completed")
        return job

    def fail_job(self, job_id: str, error: str) -> SyncJobRecord:
        job = self.get_job(job_id)
        job.status = "failed"
        job.error = error
        job.finished_at = utcnow()
        self.active_job_ids_by_key.pop(job.idempotency_key, None)
        self.active_job_ids_by_lock_key.pop(job.lock_key, None)
        self.release_job_lock(job.id)
        self.record_event(job.id, "job_failed", error)
        return job

    def record_event(self, job_id: str, stage: str, detail: str) -> SyncEventRecord:
        event = SyncEventRecord(
            id=new_id(),
            job_id=job_id,
            stage=stage,
            detail=detail,
            created_at=utcnow(),
        )
        self.events.setdefault(job_id, []).append(event)
        return event

    def job_events(self, job_id: str) -> list[SyncEventRecord]:
        return list(self.events.get(job_id, []))

    def upsert_repository(
        self,
        request: RepoRagSyncRequest,
        snapshot: RepoSnapshot,
    ) -> RepositoryRecord:
        repository_source_key = f"{source_key(request)}:{snapshot.branch}"
        repository_id = self.repository_ids_by_key.get(repository_source_key)
        now = utcnow()

        if repository_id:
            repository = self.repositories[repository_id]
            repository.name = snapshot.repository
            repository.updated_at = now
            return repository

        repository = RepositoryRecord(
            id=new_id(),
            source_key=repository_source_key,
            name=snapshot.repository,
            branch=snapshot.branch,
            repository_url=request.repository_url,
            created_at=now,
            updated_at=now,
        )
        self.repositories[repository.id] = repository
        self.repository_ids_by_key[repository_source_key] = repository.id
        return repository

    def find_repository_id(self, source_key: str) -> str | None:
        return self.repository_ids_by_key.get(source_key)

    def active_files(self, repository_id: str) -> dict[str, FileRecord]:
        active_files: dict[str, FileRecord] = {}
        for (repo_id, path), file_id in self.active_file_ids_by_path.items():
            if repo_id != repository_id:
                continue
            file = self.files[file_id]
            if file.is_active and file.deleted_at is None:
                active_files[path] = file
        return active_files

    def record_snapshot(
        self,
        repository_id: str,
        snapshot: RepoSnapshot,
    ) -> SnapshotRecord:
        record = SnapshotRecord(
            id=new_id(),
            repository_id=repository_id,
            branch=snapshot.branch,
            commit_sha=snapshot.commit_sha,
            file_count=len(snapshot.files),
            created_at=utcnow(),
        )
        self.snapshots[record.id] = record
        return record

    def apply_file_changes(
        self,
        repository_id: str,
        snapshot_id: str,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> dict[str, FileRecord]:
        now = utcnow()
        snapshot_files = {file.path: file for file in snapshot.files}
        active_files = self.active_files(repository_id)
        updated_files: dict[str, FileRecord] = {}

        for change in changes:
            active_file = active_files.get(change.path)

            if change.status == "deleted":
                if active_file:
                    self._retire_file(active_file, now)
                    self._deactivate_chunks(repository_id, change.path, now)
                continue

            if change.status == "unchanged":
                if active_file:
                    active_file.snapshot_id = snapshot_id
                    active_file.status = "unchanged"
                    active_file.last_seen_at = now
                    updated_files[change.path] = active_file
                continue

            if active_file:
                self._retire_file(active_file, now)
                self._deactivate_chunks(repository_id, change.path, now)

            snapshot_file = snapshot_files[change.path]
            file_record = FileRecord(
                id=new_id(),
                repository_id=repository_id,
                snapshot_id=snapshot_id,
                path=change.path,
                content_hash=file_hash(snapshot_file),
                status=change.status,
                is_active=True,
                last_seen_at=now,
            )
            self.files[file_record.id] = file_record
            self.active_file_ids_by_path[(repository_id, change.path)] = file_record.id
            updated_files[change.path] = file_record

        return updated_files

    def upsert_chunks(
        self,
        repository_id: str,
        snapshot_id: str,
        file_records: dict[str, FileRecord],
        chunks: list[EmbeddedChunk],
    ) -> list[ChunkRecord]:
        now = utcnow()
        records: list[ChunkRecord] = []

        for embedded in chunks:
            chunk = embedded.chunk
            file_record = file_records[chunk.source_path]
            chunk_hash = hash_text(f"{chunk.source_path}\0{chunk.text}\0{chunk.citation}")
            record = ChunkRecord(
                id=chunk.id,
                repository_id=repository_id,
                file_id=file_record.id,
                snapshot_id=snapshot_id,
                source_path=chunk.source_path,
                chunk_hash=chunk_hash,
                text=chunk.text,
                citation=chunk.citation,
                is_active=True,
                created_at=now,
                chunk_type=chunk.chunk_type,
                symbol_name=chunk.symbol_name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
            )
            self.chunks[record.id] = record
            records.append(record)

        return records

    def active_chunks(self, repository_id: str) -> list[RetrievalChunk]:
        chunks = [
            chunk.to_chunk()
            for chunk in self.chunks.values()
            if chunk.repository_id == repository_id and chunk.is_active and chunk.deleted_at is None
        ]
        return sorted(chunks, key=lambda chunk: chunk.source_path)

    def hard_delete_inactive(self, batch_size: int, cutoff: datetime) -> int:
        deleted = 0

        for chunk_id, chunk in list(self.chunks.items()):
            if deleted >= batch_size:
                return deleted
            if not chunk.is_active and chunk.deleted_at and chunk.deleted_at <= cutoff:
                del self.chunks[chunk_id]
                deleted += 1

        active_chunk_file_ids = {chunk.file_id for chunk in self.chunks.values()}
        for file_id, file in list(self.files.items()):
            if deleted >= batch_size:
                return deleted
            if (
                not file.is_active
                and file.deleted_at
                and file.deleted_at <= cutoff
                and file.id not in active_chunk_file_ids
            ):
                del self.files[file_id]
                deleted += 1

        return deleted

    def _retire_file(self, file: FileRecord, now: datetime) -> None:
        file.is_active = False
        file.deleted_at = now
        self.active_file_ids_by_path.pop((file.repository_id, file.path), None)

    def _deactivate_chunks(self, repository_id: str, source_path: str, now: datetime) -> None:
        for chunk in self.chunks.values():
            if (
                chunk.repository_id == repository_id
                and chunk.source_path == source_path
                and chunk.is_active
            ):
                chunk.is_active = False
                chunk.deleted_at = now
