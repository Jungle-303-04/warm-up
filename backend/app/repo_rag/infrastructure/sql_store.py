"""SQLAlchemy/Postgres 기반 RepoRagStore 구현.

InMemoryRepoRagStore와 동일한 책임/알고리즘을 Postgres로 옮긴 어댑터다.
요청 단위 Session을 주입받아 사용하며, 트랜잭션 경계(commit/rollback)는
세션을 제공하는 FastAPI 의존성이 관리한다(저장소는 commit 하지 않는다).
sqlalchemy/pgvector에 의존하므로 Postgres 경로에서만 import 한다.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.pipeline.router import RepoSnapshot, RetrievalChunk
from app.repo_rag.api.schemas import RepoFileChange, RepoRagSyncRequest
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
from app.repo_rag.infrastructure.mappers import (
    to_chunk_record as _to_chunk_record,
)
from app.repo_rag.infrastructure.mappers import (
    to_event_record as _to_event_record,
)
from app.repo_rag.infrastructure.mappers import (
    to_file_record as _to_file_record,
)
from app.repo_rag.infrastructure.mappers import (
    to_job_record as _to_job_record,
)
from app.repo_rag.infrastructure.mappers import (
    to_repository_record as _to_repository_record,
)
from app.repo_rag.infrastructure.mappers import (
    to_snapshot_record as _to_snapshot_record,
)
from app.repo_rag.infrastructure.models import (
    ChunkModel,
    EventModel,
    FileModel,
    JobModel,
    RepositoryModel,
    SnapshotModel,
    active_filters,
)

ACTIVE_JOB_STATUSES = (
    "queued",
    "running",
    "running_sync",
    "running_code_index",
    "running_rag_index",
    "running_agent_proposal",
)


class SqlRepoRagStore:
    def __init__(self, session: Session) -> None:
        self._db = session

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """주입된 요청 단위 세션을 그대로 사용한다.

        commit/rollback은 세션을 제공하는 FastAPI 의존성이 담당하므로, 한 요청
        안의 모든 저장소 호출이 하나의 트랜잭션을 공유한다(원자적 sync)."""
        yield self._db

    # ---- jobs -------------------------------------------------------------

    def create_job(self, request: RepoRagSyncRequest) -> SyncJobRecord:
        request_idempotency_key = idempotency_key(request)
        request_lock_key = lock_key(request)

        with self._session() as session:
            existing = self._find_active_job(
                session, idempotency_key=request_idempotency_key, lock_key=request_lock_key
            )
            if existing is not None:
                return _to_job_record(existing)

            job = JobModel(
                id=new_id(),
                trigger_type=request.trigger_type,
                branch=request.branch,
                idempotency_key=request_idempotency_key,
                lock_key=request_lock_key,
                requested_commit_sha=request.requested_commit_sha,
                status="queued",
                request_json=request.model_dump(mode="json"),
                created_at=utcnow(),
            )
            session.add(job)
            self._add_event(
                session, job.id, "job_queued", f"{request.trigger_type} sync job queued"
            )
            session.flush()
            return _to_job_record(job)

    def claim_next_queued_job(self) -> SyncJobRecord | None:
         return self.claim_next_job_by_status("queued")

    def claim_next_job_by_status(self, status: str) -> SyncJobRecord | None:
        with self._session() as session:
            job = session.scalars(
                select(JobModel)
                .where(JobModel.status == status)
                .order_by(JobModel.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).first()
            if job is None:
                return None
            
            # 선점 상태 천이 표시
            if status == "queued":
                job.status = "running_sync"
            elif status == "running_sync":
                job.status = "running_code_index"
            elif status == "running_code_index":
                job.status = "running_rag_index"
            elif status == "running_rag_index":
                job.status = "running_agent_proposal"
                
            self._add_event(session, job.id, f"job_claimed_{status}", f"claimed stage {status}")
            session.flush()
            return _to_job_record(job)

    def update_job_status(self, job_id: str, status: str) -> SyncJobRecord:
        with self._session() as session:
            job = self._require_job(session, job_id)
            job.status = status
            self._add_event(session, job.id, "status_changed", f"job status changed to {status}")
            session.flush()
            return _to_job_record(job)

    def get_job(self, job_id: str) -> SyncJobRecord:
        with self._session() as session:
            return _to_job_record(self._require_job(session, job_id))

    def start_job(self, job_id: str) -> SyncJobRecord:
        with self._session() as session:
            job = self._require_job(session, job_id)
            if job.status == "queued":
                job.status = "running_sync"
            job.started_at = job.started_at or utcnow()
            self._add_event(session, job.id, "job_started", "sync worker started")
            session.flush()
            return _to_job_record(job)

    def start_job_stage(self, job_id: str, status: str) -> SyncJobRecord:
        with self._session() as session:
            job = self._require_job(session, job_id)
            job.status = status
            job.started_at = job.started_at or utcnow()
            self._add_event(session, job.id, f"stage_started_{status}", f"started stage {status}")
            session.flush()
            return _to_job_record(job)

    def claim_job_lock(self, job_id: str) -> None:
        with self._session() as session:
            job = self._require_job(session, job_id)
            running = session.scalars(
                select(JobModel).where(
                    JobModel.lock_key == job.lock_key,
                    JobModel.status == "running",
                    JobModel.id != job.id,
                )
            ).first()
            if running is not None:
                raise ValueError(f"sync already running for {job.lock_key}")
            self._add_event(session, job.id, "lock_acquired", job.lock_key)

    def release_job_lock(self, job_id: str) -> None:
        # running 상태 전이가 곧 잠금이므로 별도 해제 작업은 필요 없
        return None

    def attach_job_repository(self, job_id: str, repository_id: str) -> None:
        with self._session() as session:
            self._require_job(session, job_id).repository_id = repository_id

    def finish_job(self, job_id: str) -> SyncJobRecord:
        with self._session() as session:
            job = self._require_job(session, job_id)
            job.status = "succeeded"
            job.finished_at = utcnow()
            self._add_event(session, job.id, "job_succeeded", "sync worker completed")
            return _to_job_record(job)

    def fail_job(self, job_id: str, error: str) -> SyncJobRecord:
        with self._session() as session:
            job = self._require_job(session, job_id)
            job.status = "failed"
            job.error = error
            job.finished_at = utcnow()
            self._add_event(session, job.id, "job_failed", error)
            return _to_job_record(job)

    def record_event(self, job_id: str, stage: str, detail: str) -> SyncEventRecord:
        with self._session() as session:
            event = self._add_event(session, job_id, stage, detail)
            session.flush()
            return _to_event_record(event)

    def job_events(self, job_id: str) -> list[SyncEventRecord]:
        with self._session() as session:
            events = session.scalars(
                select(EventModel)
                .where(EventModel.job_id == job_id)
                .order_by(EventModel.created_at, EventModel.id)
            ).all()
            return [_to_event_record(event) for event in events]

    # ---- repositories / snapshots ----------------------------------------

    def upsert_repository(
        self,
        request: RepoRagSyncRequest,
        snapshot: RepoSnapshot,
    ) -> RepositoryRecord:
        repository_source_key = f"{source_key(request)}:{snapshot.branch}"
        now = utcnow()

        with self._session() as session:
            repository = session.scalars(
                select(RepositoryModel).where(RepositoryModel.source_key == repository_source_key)
            ).first()

            if repository is not None:
                repository.name = snapshot.repository
                repository.updated_at = now
            else:
                repository = RepositoryModel(
                    id=new_id(),
                    source_key=repository_source_key,
                    name=snapshot.repository,
                    branch=snapshot.branch,
                    repository_url=request.repository_url,
                    created_at=now,
                    updated_at=now,
                )
                session.add(repository)

            session.flush()
            return _to_repository_record(repository)

    def record_snapshot(
        self,
        repository_id: str,
        snapshot: RepoSnapshot,
    ) -> SnapshotRecord:
        with self._session() as session:
            record = SnapshotModel(
                id=new_id(),
                repository_id=repository_id,
                branch=snapshot.branch,
                commit_sha=snapshot.commit_sha,
                file_count=len(snapshot.files),
                created_at=utcnow(),
            )
            session.add(record)
            session.flush()
            return _to_snapshot_record(record)

    def find_repository_id(self, source_key: str) -> str | None:
        with self._session() as session:
            repository = session.scalars(
                select(RepositoryModel).where(RepositoryModel.source_key == source_key)
            ).first()
            return repository.id if repository is not None else None

    # ---- files ------------------------------------------------------------

    def active_files(self, repository_id: str) -> dict[str, FileRecord]:
        with self._session() as session:
            models = self._active_file_models(session, repository_id)
            return {model.path: _to_file_record(model) for model in models}

    def apply_file_changes(
        self,
        repository_id: str,
        snapshot_id: str,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> dict[str, FileRecord]:
        now = utcnow()
        snapshot_files = {file.path: file for file in snapshot.files}
        updated: dict[str, FileRecord] = {}

        with self._session() as session:
            active_files = {
                model.path: model for model in self._active_file_models(session, repository_id)
            }

            for change in changes:
                active_file = active_files.get(change.path)

                if change.status == "deleted":
                    if active_file is not None:
                        self._retire_file(session, active_file, now)
                        self._deactivate_chunks(session, repository_id, change.path, now)
                    continue

                if change.status == "unchanged":
                    if active_file is not None:
                        active_file.snapshot_id = snapshot_id
                        active_file.status = "unchanged"
                        active_file.last_seen_at = now
                        updated[change.path] = _to_file_record(active_file)
                    continue

                if active_file is not None:
                    self._retire_file(session, active_file, now)
                    self._deactivate_chunks(session, repository_id, change.path, now)

                snapshot_file = snapshot_files[change.path]
                file_model = FileModel(
                    id=new_id(),
                    repository_id=repository_id,
                    snapshot_id=snapshot_id,
                    path=change.path,
                    content_hash=file_hash(snapshot_file),
                    status=change.status,
                    is_active=True,
                    last_seen_at=now,
                )
                session.add(file_model)
                session.flush()
                updated[change.path] = _to_file_record(file_model)

        return updated

    # ---- chunks -----------------------------------------------------------

    def upsert_chunks(
        self,
        repository_id: str,
        snapshot_id: str,
        file_records: dict[str, FileRecord],
        chunks: list[EmbeddedChunk],
    ) -> list[ChunkRecord]:
        if not chunks:
            return []

        now = utcnow()
        records: list[ChunkRecord] = []

        with self._session() as session:
            for embedded in chunks:
                chunk = embedded.chunk
                file_record = file_records[chunk.source_path]
                chunk_hash = hash_text(f"{chunk.source_path}\0{chunk.text}\0{chunk.citation}")
                model = ChunkModel(
                    id=chunk.id,
                    repository_id=repository_id,
                    file_id=file_record.id,
                    snapshot_id=snapshot_id,
                    source_path=chunk.source_path,
                    chunk_hash=chunk_hash,
                    text=chunk.text,
                    citation=chunk.citation,
                    chunk_type=chunk.chunk_type,
                    symbol_name=chunk.symbol_name,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    language=chunk.language,
                    embedding=embedded.embedding,
                    is_active=True,
                    created_at=now,
                )
                session.merge(model)
                records.append(_to_chunk_record(model))

        return records

    def active_chunks(self, repository_id: str) -> list[RetrievalChunk]:
        with self._session() as session:
            models = session.scalars(
                select(ChunkModel)
                .where(
                    ChunkModel.repository_id == repository_id,
                    *active_filters(ChunkModel),
                )
                .order_by(ChunkModel.source_path)
            ).all()
            return [_to_chunk_record(model).to_chunk() for model in models]

    def hard_delete_inactive(self, batch_size: int, cutoff: datetime) -> int:
        deleted = 0

        with self._session() as session:
            chunk_ids = session.scalars(
                select(ChunkModel.id)
                .where(
                    ChunkModel.is_active.is_(False),
                    ChunkModel.deleted_at.is_not(None),
                    ChunkModel.deleted_at <= cutoff,
                )
                .limit(batch_size)
            ).all()
            if chunk_ids:
                session.execute(delete(ChunkModel).where(ChunkModel.id.in_(chunk_ids)))
                deleted += len(chunk_ids)

            if deleted >= batch_size:
                return deleted

            referenced_file_ids = set(session.scalars(select(ChunkModel.file_id).distinct()).all())
            file_ids = [
                file_id
                for file_id in session.scalars(
                    select(FileModel.id)
                    .where(
                        FileModel.is_active.is_(False),
                        FileModel.deleted_at.is_not(None),
                        FileModel.deleted_at <= cutoff,
                    )
                    .limit(batch_size - deleted)
                ).all()
                if file_id not in referenced_file_ids
            ]
            if file_ids:
                session.execute(delete(FileModel).where(FileModel.id.in_(file_ids)))
                deleted += len(file_ids)

        return deleted

    # ---- helpers ----------------------------------------------------------

    def _find_active_job(
        self,
        session: Session,
        *,
        idempotency_key: str,
        lock_key: str,
    ) -> JobModel | None:
        by_idempotency = session.scalars(
            select(JobModel)
            .where(
                JobModel.idempotency_key == idempotency_key,
                JobModel.status.in_(ACTIVE_JOB_STATUSES),
            )
            .order_by(JobModel.created_at.desc())
        ).first()
        if by_idempotency is not None:
            return by_idempotency

        return session.scalars(
            select(JobModel)
            .where(
                JobModel.lock_key == lock_key,
                JobModel.status.in_(ACTIVE_JOB_STATUSES),
            )
            .order_by(JobModel.created_at.desc())
        ).first()

    def _require_job(self, session: Session, job_id: str) -> JobModel:
        job = session.get(JobModel, job_id)
        if job is None:
            raise KeyError(job_id)
        return job

    def _add_event(self, session: Session, job_id: str, stage: str, detail: str) -> EventModel:
        event = EventModel(
            id=new_id(),
            job_id=job_id,
            stage=stage,
            detail=detail,
            created_at=utcnow(),
        )
        session.add(event)
        return event

    def _active_file_models(self, session: Session, repository_id: str) -> list[FileModel]:
        return list(
            session.scalars(
                select(FileModel).where(
                    FileModel.repository_id == repository_id,
                    *active_filters(FileModel),
                )
            ).all()
        )

    def _retire_file(self, session: Session, file_model: FileModel, now: datetime) -> None:
        file_model.is_active = False
        file_model.deleted_at = now

    def _deactivate_chunks(
        self,
        session: Session,
        repository_id: str,
        source_path: str,
        now: datetime,
    ) -> None:
        chunks = session.scalars(
            select(ChunkModel).where(
                ChunkModel.repository_id == repository_id,
                ChunkModel.source_path == source_path,
                ChunkModel.is_active.is_(True),
            )
        ).all()
        for chunk in chunks:
            chunk.is_active = False
            chunk.deleted_at = now
