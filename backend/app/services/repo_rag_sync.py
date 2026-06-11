from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from app.schemas.pipeline import PipelineRequest, RepoFile, RepoSnapshot, RetrievalChunk
from app.schemas.repo_rag import (
    RepoFileChange,
    RepoRagSyncRequest,
    RepoRagSyncResponse,
    SyncEventView,
    SyncJobStatus,
    SyncJobView,
    SyncTriggerType,
)
from app.services.repo_sync import RepoSyncService


ACTIVE_JOB_STATUSES: set[SyncJobStatus] = {"queued", "running"}
CHUNK_TEXT_LIMIT = 800


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return str(uuid4())


def _hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _file_hash(file: RepoFile) -> str:
    return _hash_text(file.content)


def _source_key(request: PipelineRequest) -> str:
    if request.repository_url:
        return request.repository_url.strip()
    if request.repository_path:
        return request.repository_path.strip()
    return request.repository


def _idempotency_key(request: RepoRagSyncRequest) -> str:
    requested_commit = request.requested_commit_sha or "latest"
    return ":".join(
        [
            _source_key(request),
            request.branch,
            request.trigger_type,
            requested_commit,
        ]
    )


def _lock_key(request: PipelineRequest) -> str:
    return f"{_source_key(request)}:{request.branch}"


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

    def to_chunk(self) -> RetrievalChunk:
        return RetrievalChunk(
            id=self.id,
            source_path=self.source_path,
            text=self.text,
            citation=self.citation,
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
    created_at: datetime = field(default_factory=_utcnow)
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


class RepoDiffService:
    def compare(
        self,
        previous_files: dict[str, FileRecord],
        snapshot: RepoSnapshot,
    ) -> list[RepoFileChange]:
        current_hashes = {file.path: _file_hash(file) for file in snapshot.files}
        paths = sorted(previous_files.keys() | current_hashes.keys())
        changes: list[RepoFileChange] = []

        for path in paths:
            previous = previous_files.get(path)
            current_hash = current_hashes.get(path)

            if previous is None and current_hash is not None:
                status = "added"
            elif previous is not None and current_hash is None:
                status = "deleted"
            elif previous is not None and previous.content_hash != current_hash:
                status = "modified"
            else:
                status = "unchanged"

            changes.append(
                RepoFileChange(
                    path=path,
                    status=status,
                    previous_hash=previous.content_hash if previous else None,
                    current_hash=current_hash,
                )
            )

        return changes


class ChunkingService:
    def chunk_changed_files(
        self,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> list[RetrievalChunk]:
        changed_paths = {
            change.path for change in changes if change.status in {"added", "modified"}
        }
        chunks: list[RetrievalChunk] = []

        for file in snapshot.files:
            if file.path not in changed_paths:
                continue

            text = file.content.strip()
            if not text:
                continue

            chunk_text = text[:CHUNK_TEXT_LIMIT]
            chunk_hash = _hash_text(f"{file.path}\0{_file_hash(file)}\0{chunk_text}")[:16]
            chunks.append(
                RetrievalChunk(
                    id=f"{file.path}@{snapshot.commit_sha}:{chunk_hash}",
                    source_path=file.path,
                    text=chunk_text,
                    citation=f"{snapshot.repository}:{file.path}@{snapshot.commit_sha}",
                )
            )

        return chunks


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
        idempotency_key = _idempotency_key(request)
        active_job_id = self.active_job_ids_by_key.get(idempotency_key)
        if active_job_id:
            active_job = self.jobs[active_job_id]
            if active_job.status in ACTIVE_JOB_STATUSES:
                return active_job

        lock_key = _lock_key(request)
        active_job_id = self.active_job_ids_by_lock_key.get(lock_key)
        if active_job_id:
            active_job = self.jobs[active_job_id]
            if active_job.status in ACTIVE_JOB_STATUSES:
                return active_job

        job = SyncJobRecord(
            id=_new_id(),
            trigger_type=request.trigger_type,
            branch=request.branch,
            requested_commit_sha=request.requested_commit_sha,
            idempotency_key=idempotency_key,
            lock_key=lock_key,
            request=request,
        )
        self.jobs[job.id] = job
        self.active_job_ids_by_key[idempotency_key] = job.id
        self.active_job_ids_by_lock_key[lock_key] = job.id
        self.record_event(job.id, "job_queued", f"{request.trigger_type} sync job queued")
        return job

    def get_job(self, job_id: str) -> SyncJobRecord:
        return self.jobs[job_id]

    def start_job(self, job_id: str) -> SyncJobRecord:
        job = self.get_job(job_id)
        job.status = "running"
        job.started_at = job.started_at or _utcnow()
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
        job.finished_at = _utcnow()
        self.active_job_ids_by_key.pop(job.idempotency_key, None)
        self.active_job_ids_by_lock_key.pop(job.lock_key, None)
        self.release_job_lock(job.id)
        self.record_event(job.id, "job_succeeded", "sync worker completed")
        return job

    def fail_job(self, job_id: str, error: str) -> SyncJobRecord:
        job = self.get_job(job_id)
        job.status = "failed"
        job.error = error
        job.finished_at = _utcnow()
        self.active_job_ids_by_key.pop(job.idempotency_key, None)
        self.active_job_ids_by_lock_key.pop(job.lock_key, None)
        self.release_job_lock(job.id)
        self.record_event(job.id, "job_failed", error)
        return job

    def record_event(self, job_id: str, stage: str, detail: str) -> SyncEventRecord:
        event = SyncEventRecord(
            id=_new_id(),
            job_id=job_id,
            stage=stage,
            detail=detail,
            created_at=_utcnow(),
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
        source_key = f"{_source_key(request)}:{snapshot.branch}"
        repository_id = self.repository_ids_by_key.get(source_key)
        now = _utcnow()

        if repository_id:
            repository = self.repositories[repository_id]
            repository.name = snapshot.repository
            repository.updated_at = now
            return repository

        repository = RepositoryRecord(
            id=_new_id(),
            source_key=source_key,
            name=snapshot.repository,
            branch=snapshot.branch,
            repository_url=request.repository_url,
            created_at=now,
            updated_at=now,
        )
        self.repositories[repository.id] = repository
        self.repository_ids_by_key[source_key] = repository.id
        return repository

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
            id=_new_id(),
            repository_id=repository_id,
            branch=snapshot.branch,
            commit_sha=snapshot.commit_sha,
            file_count=len(snapshot.files),
            created_at=_utcnow(),
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
        now = _utcnow()
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
                id=_new_id(),
                repository_id=repository_id,
                snapshot_id=snapshot_id,
                path=change.path,
                content_hash=_file_hash(snapshot_file),
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
        chunks: list[RetrievalChunk],
    ) -> list[ChunkRecord]:
        now = _utcnow()
        records: list[ChunkRecord] = []

        for chunk in chunks:
            file_record = file_records[chunk.source_path]
            chunk_hash = _hash_text(f"{chunk.source_path}\0{chunk.text}\0{chunk.citation}")
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
            )
            self.chunks[record.id] = record
            records.append(record)

        return records

    def active_chunks(self, repository_id: str) -> list[RetrievalChunk]:
        chunks = [
            chunk.to_chunk()
            for chunk in self.chunks.values()
            if chunk.repository_id == repository_id
            and chunk.is_active
            and chunk.deleted_at is None
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


@dataclass(slots=True)
class SyncJobProducer:
    store: InMemoryRepoRagStore

    def enqueue(self, request: RepoRagSyncRequest) -> SyncJobRecord:
        return self.store.create_job(request)

    def enqueue_manual(self, request: PipelineRequest) -> SyncJobRecord:
        return self.enqueue(_repo_rag_request(request, trigger_type="manual"))

    def enqueue_schedule(self, request: PipelineRequest) -> SyncJobRecord:
        return self.enqueue(_repo_rag_request(request, trigger_type="schedule"))

    def enqueue_webhook(
        self,
        request: PipelineRequest,
        requested_commit_sha: str,
    ) -> SyncJobRecord:
        return self.enqueue(
            _repo_rag_request(
                request,
                trigger_type="webhook",
                requested_commit_sha=requested_commit_sha,
            )
        )


@dataclass(slots=True)
class SyncWorker:
    store: InMemoryRepoRagStore
    repo_sync: RepoSyncService = field(default_factory=RepoSyncService)
    diff: RepoDiffService = field(default_factory=RepoDiffService)
    chunking: ChunkingService = field(default_factory=ChunkingService)

    def run(self, job_id: str) -> RepoRagSyncResponse:
        job = self.store.start_job(job_id)

        try:
            self.store.claim_job_lock(job.id)
            self.store.record_event(job.id, "fetch_started", "fetching repository snapshot")
            snapshot = self.repo_sync.sync(job.request)
            self.store.record_event(
                job.id,
                "fetch_completed",
                f"{snapshot.repository}@{snapshot.commit_sha}",
            )

            repository = self.store.upsert_repository(job.request, snapshot)
            self.store.attach_job_repository(job.id, repository.id)
            previous_files = self.store.active_files(repository.id)
            snapshot_record = self.store.record_snapshot(repository.id, snapshot)

            changes = self.diff.compare(previous_files, snapshot)
            self.store.record_event(job.id, "diff_completed", _change_summary(changes))

            file_records = self.store.apply_file_changes(
                repository.id,
                snapshot_record.id,
                snapshot,
                changes,
            )
            self.store.record_event(job.id, "files_persisted", f"{len(file_records)} active files")

            chunks = self.chunking.chunk_changed_files(snapshot, changes)
            chunk_records = self.store.upsert_chunks(
                repository.id,
                snapshot_record.id,
                file_records,
                chunks,
            )
            self.store.record_event(job.id, "chunks_upserted", f"{len(chunk_records)} chunks")

            job = self.store.finish_job(job.id)
            return RepoRagSyncResponse(
                job=job.to_view(),
                repository=snapshot,
                changes=changes,
                active_chunks=self.store.active_chunks(repository.id),
                events=[event.to_view() for event in self.store.job_events(job.id)],
            )
        except Exception as exc:
            self.store.fail_job(job.id, str(exc))
            raise


@dataclass(slots=True)
class RetentionCleanupService:
    store: InMemoryRepoRagStore

    def cleanup(self, *, batch_size: int, cutoff: datetime) -> int:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        return self.store.hard_delete_inactive(batch_size=batch_size, cutoff=cutoff)


@dataclass(slots=True)
class RepoRagSyncService:
    store: InMemoryRepoRagStore = field(default_factory=InMemoryRepoRagStore)
    producer: SyncJobProducer = field(init=False)
    worker: SyncWorker = field(init=False)
    cleanup: RetentionCleanupService = field(init=False)

    def __post_init__(self) -> None:
        self.producer = SyncJobProducer(self.store)
        self.worker = SyncWorker(self.store)
        self.cleanup = RetentionCleanupService(self.store)

    def run(self, request: RepoRagSyncRequest) -> RepoRagSyncResponse:
        job = self.producer.enqueue(request)
        return self.worker.run(job.id)


def _repo_rag_request(
    request: PipelineRequest,
    *,
    trigger_type: SyncTriggerType,
    requested_commit_sha: str | None = None,
) -> RepoRagSyncRequest:
    payload = request.model_dump()
    payload["trigger_type"] = trigger_type
    payload["requested_commit_sha"] = requested_commit_sha
    return RepoRagSyncRequest.model_validate(payload)


def _change_summary(changes: list[RepoFileChange]) -> str:
    counts = {"added": 0, "modified": 0, "deleted": 0, "unchanged": 0}
    for change in changes:
        counts[change.status] += 1
    return ", ".join(f"{status}={count}" for status, count in counts.items())
