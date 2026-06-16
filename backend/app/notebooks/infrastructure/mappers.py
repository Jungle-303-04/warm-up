"""레코드 ↔ ORM 변환(도메인 ↔ ORM 경계)."""

from typing import cast

from app.notebooks.domain.records import (
    ChatMessageRecord,
    ChatRole,
    NotebookRecord,
    SourceKind,
    SourceRecord,
)
from app.notebooks.infrastructure.models import ChatMessageModel, NotebookModel, SourceModel


def notebook_to_model(record: NotebookRecord) -> NotebookModel:
    return NotebookModel(
        id=record.id,
        title=record.title,
        summary=record.summary,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def notebook_to_record(model: NotebookModel) -> NotebookRecord:
    return NotebookRecord(
        id=model.id,
        title=model.title,
        summary=model.summary,
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
