"""노트북/소스 영속 레코드.

노트북은 여러 소스(md/text/url/pdf/repo)를 묶는 컨테이너다.
repo 소스는 clone 결과를 repo_snapshot(list[{path, content}])로 캐시해
트리/파일 조회를 git 재호출 없이 처리한다.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

SourceKind = Literal["md", "text", "url", "pdf", "repo"]


@dataclass(slots=True)
class NotebookRecord:
    id: str
    title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime


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
