"""ORM 모델 → 도메인 레코드 변환기.

저장소(sql_store)와 리트리버(sql_retriever)가 공유하므로 별도 모듈로 분리해
서로 직접 의존하지 않게 한다.
"""

from typing import cast

from app.repo_rag.api.schemas import (
    RepoRagSyncRequest,
    SyncJobStatus,
    SyncTriggerType,
)
from app.repo_rag.domain.records import (
    ChunkRecord,
    FileRecord,
    RepositoryRecord,
    SnapshotRecord,
    SyncEventRecord,
    SyncJobRecord,
)
from app.repo_rag.infrastructure.models import (
    ChunkModel,
    EventModel,
    FileModel,
    JobModel,
    RepositoryModel,
    SnapshotModel,
)


def to_job_record(model: JobModel) -> SyncJobRecord:
    return SyncJobRecord(
        id=model.id,
        trigger_type=cast(SyncTriggerType, model.trigger_type),
        branch=model.branch,
        idempotency_key=model.idempotency_key,
        lock_key=model.lock_key,
        request=RepoRagSyncRequest.model_validate(model.request_json),
        repository_id=model.repository_id,
        requested_commit_sha=model.requested_commit_sha,
        status=cast(SyncJobStatus, model.status),
        error=model.error,
        created_at=model.created_at,
        started_at=model.started_at,
        finished_at=model.finished_at,
    )


def to_event_record(model: EventModel) -> SyncEventRecord:
    return SyncEventRecord(
        id=model.id,
        job_id=model.job_id,
        stage=model.stage,
        detail=model.detail,
        created_at=model.created_at,
    )


def to_repository_record(model: RepositoryModel) -> RepositoryRecord:
    return RepositoryRecord(
        id=model.id,
        source_key=model.source_key,
        name=model.name,
        branch=model.branch,
        repository_url=model.repository_url,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_snapshot_record(model: SnapshotModel) -> SnapshotRecord:
    return SnapshotRecord(
        id=model.id,
        repository_id=model.repository_id,
        branch=model.branch,
        commit_sha=model.commit_sha,
        file_count=model.file_count,
        created_at=model.created_at,
    )


def to_file_record(model: FileModel) -> FileRecord:
    return FileRecord(
        id=model.id,
        repository_id=model.repository_id,
        snapshot_id=model.snapshot_id,
        path=model.path,
        content_hash=model.content_hash,
        status=model.status,
        is_active=model.is_active,
        last_seen_at=model.last_seen_at,
        deleted_at=model.deleted_at,
    )


def to_chunk_record(model: ChunkModel) -> ChunkRecord:
    return ChunkRecord(
        id=model.id,
        repository_id=model.repository_id,
        file_id=model.file_id,
        snapshot_id=model.snapshot_id,
        source_path=model.source_path,
        chunk_hash=model.chunk_hash,
        text=model.text,
        citation=model.citation,
        is_active=model.is_active,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
        chunk_type=model.chunk_type,
        symbol_name=model.symbol_name,
        start_line=model.start_line,
        end_line=model.end_line,
        language=model.language,
    )
