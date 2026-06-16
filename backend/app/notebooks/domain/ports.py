"""노트북 저장소 포트.

도메인이 소유하는 추상. in-memory/SQL 어댑터가 구현한다(DIP).
get류는 없는 id에 대해 KeyError를 던진다(API에서 404로 변환).
"""

from typing import Protocol

from app.notebooks.domain.chunk_records import ChunkSearchHit, NotebookChunk
from app.notebooks.domain.records import ChatMessageRecord, NotebookRecord, SourceRecord


class NotebookStore(Protocol):
    def add_notebook(self, record: NotebookRecord) -> None: ...

    def get_notebook(self, notebook_id: str) -> NotebookRecord: ...

    def list_notebooks(self) -> list[NotebookRecord]: ...

    def update_notebook(self, record: NotebookRecord) -> None: ...

    def delete_notebook(self, notebook_id: str) -> None: ...

    def add_source(self, record: SourceRecord) -> None: ...

    def list_sources(self, notebook_id: str) -> list[SourceRecord]: ...

    def get_source(self, notebook_id: str, source_id: str) -> SourceRecord: ...

    def delete_source(self, notebook_id: str, source_id: str) -> None: ...

    def add_chat_message(self, record: ChatMessageRecord) -> None: ...

    def list_chat_messages(self, notebook_id: str) -> list[ChatMessageRecord]: ...

    def clear_chat_messages(self, notebook_id: str) -> None: ...


class ChunkStore(Protocol):
    """노트북 청크 영속 저장소 포트.

    add_many/delete_by_source는 인덱싱 파이프라인이, search는 채팅이 사용한다.
    search는 (벡터 코사인 + 키워드)로 점수를 매겨 상위 청크를 돌려준다.
    """

    def add_many(self, chunks: list[NotebookChunk]) -> None: ...

    def delete_by_source(self, source_id: str) -> None: ...

    def count_by_source(self, source_id: str) -> int: ...

    def search(
        self,
        notebook_id: str,
        *,
        query_embedding: list[float] | None,
        query_text: str,
        source_ids: list[str] | None,
        top_k: int,
        file_paths: list[str] | None = None,
    ) -> list[ChunkSearchHit]: ...
