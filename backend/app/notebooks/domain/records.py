"""노트북/소스 영속 레코드.

노트북은 여러 소스(md/text/url/pdf/repo)를 묶는 컨테이너다.
repo 소스는 clone 결과를 repo_snapshot(list[{path, content}])로 캐시해
트리/파일 조회를 git 재호출 없이 처리한다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

SourceKind = Literal["md", "text", "url", "pdf", "repo"]
ChatRole = Literal["user", "assistant"]


@dataclass(slots=True)
class NotebookRecord:
    id: str
    title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime
    sources: list["SourceRecord"] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.sources)


@dataclass(slots=True)
class SourceRecord:
    id: str
    notebook_id: str
    kind: SourceKind
    title: str
    created_at: datetime
    content: str | None = None
    url: str | None = None
    repository_url: str | None = None
    branch: str | None = None
    # repo 전용 캐시: [{"path": ..., "content": ...}, ...]
    repo_snapshot: list[dict] | None = field(default=None)


@dataclass(slots=True)
class ChatMessageRecord:
    id: str
    notebook_id: str
    role: ChatRole
    content: str
    created_at: datetime
    citations: list[dict] = field(default_factory=list)
    source_ids: list[str] | None = None
