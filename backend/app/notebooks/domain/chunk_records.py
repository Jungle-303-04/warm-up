"""노트북 청크 영속 레코드와 검색 결과.

소스를 RAG로 인덱싱하면 파일/문단 단위 청크가 생성되고, 각 청크는 임베딩
벡터(없을 수도 있음)와 함께 ChunkStore에 저장된다. 채팅은 질문 임베딩으로
이 청크들을 검색해 근거로 삼는다.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class NotebookChunk:
    id: str
    notebook_id: str
    source_id: str
    chunk_index: int
    text: str
    file_path: str | None = None
    language: str | None = None
    format: str | None = None
    heading_path: list[str] | None = None
    page: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    content_hash: str | None = None
    parent_chunk_id: str | None = None
    prev_chunk_id: str | None = None
    next_chunk_id: str | None = None
    embedding: list[float] | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ChunkSearchHit:
    """검색 점수가 매겨진 청크."""

    chunk: NotebookChunk
    score: float
    matched_terms: list[str] = field(default_factory=list)
