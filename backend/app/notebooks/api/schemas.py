from datetime import datetime

from pydantic import BaseModel

from app.notebooks.domain.records import NotebookRecord, SourceKind, SourceRecord


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


class TreeResponse(BaseModel):
    tree: list[TreeNode]


class FileResponse(BaseModel):
    path: str
    content: str
