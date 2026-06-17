"""노트북 저장소 포트.

도메인이 소유하는 추상. in-memory/SQL 어댑터가 구현한다(DIP).
get류는 없는 id에 대해 KeyError를 던진다(API에서 404로 변환).
"""

from collections.abc import Callable
from typing import Any, Protocol

from app.notebooks.domain.chunk_records import ChunkSearchHit, NotebookChunk
from app.notebooks.domain.indexing_progress import IndexProgress
from app.notebooks.domain.records import ChatMessageRecord, NotebookRecord, SourceRecord


class NotebookStore(Protocol):
    def add_notebook(self, record: NotebookRecord) -> None: ...

    def get_notebook(
        self,
        notebook_id: str,
        *,
        owner_user_id: int | None = None,
    ) -> NotebookRecord: ...

    def list_notebooks(self, *, owner_user_id: int) -> list[NotebookRecord]: ...

    def update_notebook(self, record: NotebookRecord) -> None: ...

    def delete_notebook(
        self,
        notebook_id: str,
        *,
        owner_user_id: int | None = None,
    ) -> None: ...

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

    def get_many(
        self,
        notebook_id: str,
        chunk_ids: list[str],
        *,
        source_ids: list[str] | None = None,
        file_paths: list[str] | None = None,
    ) -> list[NotebookChunk]: ...

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


class Retriever(Protocol):
    """질문과 scope를 받아 검색 hit를 반환하는 포트."""

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


class ContextExpander(Protocol):
    """검색 hit 주변의 parent/prev/next 컨텍스트를 예산 안에서 확장하는 포트."""

    def expand(
        self,
        notebook_id: str,
        hits: list[ChunkSearchHit],
        *,
        source_ids: list[str] | None,
        file_paths: list[str] | None,
    ) -> list[ChunkSearchHit]: ...


class ToolRegistry(Protocol):
    """선택된 source/file scope에 묶인 도구 목록을 만드는 포트."""

    def build(
        self,
        notebook_id: str,
        *,
        source_ids: list[str] | None,
        file_paths: list[str] | None,
    ) -> list[Any]: ...


class IndexingProgressStore(Protocol):
    """색인 진행 상태 영속/조회 포트."""

    def register(self, source_id: str, notebook_id: str) -> None: ...

    def get(self, source_id: str) -> dict | None: ...

    def remove(self, source_id: str) -> None: ...

    def update(
        self,
        source_id: str,
        mutate: Callable[[IndexProgress], None],
    ) -> None: ...

    def snapshot(self, source_id: str) -> IndexProgress | None: ...
