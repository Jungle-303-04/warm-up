"""레코드 ↔ ORM 변환(도메인 ↔ ORM 경계)."""

from typing import cast

from app.notebooks.domain.artifact_records import ArtifactRecord, ArtifactType
from app.notebooks.domain.chunk_records import NotebookChunk
from app.notebooks.domain.records import (
    ChatMessageRecord,
    ChatRole,
    NotebookRecord,
    SourceKind,
    SourceRecord,
)
from app.notebooks.infrastructure.models import (
    ArtifactModel,
    ChatMessageModel,
    NotebookChunkModel,
    NotebookModel,
    SourceModel,
)


def notebook_to_model(record: NotebookRecord) -> NotebookModel:
    return NotebookModel(
        id=record.id,
        owner_user_id=record.owner_user_id,
        title=record.title,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def notebook_to_record(model: NotebookModel) -> NotebookRecord:
    return NotebookRecord(
        id=model.id,
        owner_user_id=model.owner_user_id,
        title=model.title,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def source_to_model(record: SourceRecord) -> SourceModel:
    return SourceModel(
        id=record.id,
        notebook_id=record.notebook_id,
        kind=record.kind,
        title=record.title,
        content=record.content,
        url=record.url,
        repository_url=record.repository_url,
        branch=record.branch,
        content_hash=record.content_hash,
        derived_from_artifact_id=record.derived_from_artifact_id,
        lineage_source_ids=record.lineage_source_ids,
        repo_commits=record.repo_commits,
        repo_snapshot=record.repo_snapshot,
        created_at=record.created_at,
    )


def source_to_record(model: SourceModel) -> SourceRecord:
    return SourceRecord(
        id=model.id,
        notebook_id=model.notebook_id,
        kind=cast(SourceKind, model.kind),
        title=model.title,
        content=model.content,
        url=model.url,
        repository_url=model.repository_url,
        branch=model.branch,
        content_hash=model.content_hash,
        derived_from_artifact_id=model.derived_from_artifact_id,
        lineage_source_ids=model.lineage_source_ids,
        repo_commits=model.repo_commits,
        repo_snapshot=model.repo_snapshot,
        created_at=model.created_at,
    )


def chat_message_to_model(record: ChatMessageRecord) -> ChatMessageModel:
    return ChatMessageModel(
        id=record.id,
        notebook_id=record.notebook_id,
        role=record.role,
        content=record.content,
        citations=record.citations,
        source_ids=record.source_ids,
        created_at=record.created_at,
    )


def chat_message_to_record(model: ChatMessageModel) -> ChatMessageRecord:
    return ChatMessageRecord(
        id=model.id,
        notebook_id=model.notebook_id,
        role=cast(ChatRole, model.role),
        content=model.content,
        citations=model.citations or [],
        source_ids=model.source_ids,
        created_at=model.created_at,
    )


def chunk_to_model(record: NotebookChunk) -> NotebookChunkModel:
    return NotebookChunkModel(
        id=record.id,
        notebook_id=record.notebook_id,
        source_id=record.source_id,
        file_path=record.file_path,
        chunk_index=record.chunk_index,
        language=record.language,
        format=record.format,
        heading_path=record.heading_path,
        page=record.page,
        start_line=record.start_line,
        end_line=record.end_line,
        start_offset=record.start_offset,
        end_offset=record.end_offset,
        content_hash=record.content_hash,
        parent_chunk_id=record.parent_chunk_id,
        prev_chunk_id=record.prev_chunk_id,
        next_chunk_id=record.next_chunk_id,
        text=record.text,
        embedding=record.embedding,
        created_at=record.created_at,
    )


def chunk_to_record(model: NotebookChunkModel) -> NotebookChunk:
    embedding = model.embedding
    return NotebookChunk(
        id=model.id,
        notebook_id=model.notebook_id,
        source_id=model.source_id,
        file_path=model.file_path,
        chunk_index=model.chunk_index,
        language=model.language,
        format=model.format,
        heading_path=list(model.heading_path or []) or None,
        page=model.page,
        start_line=model.start_line,
        end_line=model.end_line,
        start_offset=model.start_offset,
        end_offset=model.end_offset,
        content_hash=model.content_hash,
        parent_chunk_id=model.parent_chunk_id,
        prev_chunk_id=model.prev_chunk_id,
        next_chunk_id=model.next_chunk_id,
        text=model.text,
        embedding=list(embedding) if embedding is not None else None,
        created_at=model.created_at,
    )


def artifact_to_model(record: ArtifactRecord) -> ArtifactModel:
    return ArtifactModel(
        id=record.id,
        notebook_id=record.notebook_id,
        type=record.type,
        title=record.title,
        content=record.content,
        source_ids=record.source_ids,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def artifact_to_record(model: ArtifactModel) -> ArtifactRecord:
    return ArtifactRecord(
        id=model.id,
        notebook_id=model.notebook_id,
        type=cast(ArtifactType, model.type),
        title=model.title,
        content=model.content,
        source_ids=list(model.source_ids or []),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
