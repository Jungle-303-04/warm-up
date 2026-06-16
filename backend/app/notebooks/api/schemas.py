from datetime import datetime

from pydantic import BaseModel

from app.notebooks.application.chat_service import ChatCitation, ChatResult
from app.notebooks.domain.records import (
    ChatMessageRecord,
    ChatRole,
    NotebookRecord,
    SourceKind,
    SourceRecord,
)


class CreateNotebookRequest(BaseModel):
    title: str
    summary: str | None = None


class UpdateNotebookRequest(BaseModel):
    title: str | None = None
    summary: str | None = None


class CreateSourceRequest(BaseModel):
    kind: SourceKind
    title: str | None = None
    content: str | None = None
    url: str | None = None
    repository_url: str | None = None
    branch: str | None = None


class ChatRequest(BaseModel):
    question: str
    source_ids: list[str] | None = None


class ChatCitationView(BaseModel):
    source_id: str
    source_title: str
    path: str | None = None
    snippet: str

    @classmethod
    def from_record(cls, record: ChatCitation) -> "ChatCitationView":
        return cls(
            source_id=record.source_id,
            source_title=record.source_title,
            path=record.path,
            snippet=record.snippet,
        )

    @classmethod
    def from_payload(cls, payload: dict) -> "ChatCitationView":
        return cls(
            source_id=str(payload.get("source_id") or ""),
            source_title=str(payload.get("source_title") or ""),
            path=payload.get("path"),
            snippet=str(payload.get("snippet") or ""),
        )


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitationView]

    @classmethod
    def from_result(cls, result: ChatResult) -> "ChatResponse":
        return cls(
            answer=result.answer,
            citations=[ChatCitationView.from_record(c) for c in result.citations],
        )


class ChatMessageView(BaseModel):
    id: str
    role: ChatRole
    content: str
    citations: list[ChatCitationView]
    source_ids: list[str] | None = None
    created_at: datetime

    @classmethod
    def from_record(cls, record: ChatMessageRecord) -> "ChatMessageView":
        return cls(
            id=record.id,
            role=record.role,
            content=record.content,
            citations=[ChatCitationView.from_payload(c) for c in record.citations],
            source_ids=record.source_ids,
            created_at=record.created_at,
        )


class ChatMessageListResponse(BaseModel):
    messages: list[ChatMessageView]


class NotebookView(BaseModel):
    id: str
    title: str
    summary: str | None = None
    source_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: NotebookRecord, *, source_count: int) -> "NotebookView":
        return cls(
            id=record.id,
            title=record.title,
            summary=record.summary,
            source_count=source_count,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class SourceView(BaseModel):
    id: str
    notebook_id: str
    kind: SourceKind
    title: str
    url: str | None = None
    repository_url: str | None = None
    branch: str | None = None
    created_at: datetime

    @classmethod
    def from_record(cls, record: SourceRecord) -> "SourceView":
        return cls(
            id=record.id,
            notebook_id=record.notebook_id,
            kind=record.kind,
            title=record.title,
            url=record.url,
            repository_url=record.repository_url,
            branch=record.branch,
            created_at=record.created_at,
        )


class SourceDetailView(SourceView):
    content: str | None = None

    @classmethod
    def from_record(cls, record: SourceRecord) -> "SourceDetailView":
        return cls(
            id=record.id,
            notebook_id=record.notebook_id,
            kind=record.kind,
            title=record.title,
            url=record.url,
            repository_url=record.repository_url,
            branch=record.branch,
            created_at=record.created_at,
            content=record.content,
        )


class NotebookDetailView(NotebookView):
    sources: list[SourceView]

    @classmethod
    def from_record(
        cls,
        record: NotebookRecord,
        *,
        sources: list[SourceRecord],
    ) -> "NotebookDetailView":
        return cls(
            id=record.id,
            title=record.title,
            summary=record.summary,
            source_count=len(sources),
            created_at=record.created_at,
            updated_at=record.updated_at,
            sources=[SourceView.from_record(s) for s in sources],
        )


class NotebookListResponse(BaseModel):
    notebooks: list[NotebookView]


class SourceListResponse(BaseModel):
    sources: list[SourceView]


class TreeNode(BaseModel):
    name: str
    path: str
    type: str  # "dir" | "file"
    children: list["TreeNode"] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        children = data.get("children")
        if children:
            children = [cls.from_dict(child) for child in children]
        return cls(
            name=data["name"],
            path=data["path"],
            type=data["type"],
            children=children
        )


class TreeResponse(BaseModel):
    tree: list[TreeNode]


class FileResponse(BaseModel):
    path: str
    content: str
