"""산출물(artifact) 영속 레코드.

노트북의 소스들로부터 생성한 다이어그램/요약/메모를 표현한다.
- uml/erd/dependency: content는 Mermaid 다이어그램 텍스트.
- change_summary: content는 마크다운(+선택적 Mermaid).
- note: 사용자가 직접 작성한 메모(생성 기준 소스가 없을 수 있어 source_ids는 빈 배열 허용).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

ArtifactType = Literal["uml", "erd", "dependency", "change_summary", "note"]


@dataclass(slots=True)
class ArtifactRecord:
    id: str
    notebook_id: str
    type: ArtifactType
    title: str
    content: str
    # 생성 기준이 된 소스 id 배열. note는 빈 배열일 수 있음
    source_ids: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
