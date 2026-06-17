"""노트북 및 아티팩트 저장소/생성기 포트 인터페이스 정의."""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.notebooks.domain import (
    ArtifactRecord,
    ArtifactType,
    ChatMessageRecord,
    ChunkSearchHit,
    NotebookChunk,
    NotebookRecord,
    SourceRecord,
)


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


class ArtifactStore(Protocol):
    def add(self, record: ArtifactRecord) -> None: ...

    def get(self, notebook_id: str, artifact_id: str) -> ArtifactRecord: ...

    def list_by_notebook(self, notebook_id: str) -> list[ArtifactRecord]: ...

    def update(self, record: ArtifactRecord) -> None: ...

    def delete(self, notebook_id: str, artifact_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class ArtifactContext:
    """산출물 생성에 전달되는 코드/문서 컨텍스트(한 청크 단위)."""

    source_id: str
    source_title: str
    text: str
    path: str | None = None
    language: str | None = None


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """산출물 생성 요청(포트로 전달되는 순수 값)."""

    type: ArtifactType
    contexts: list[ArtifactContext] = field(default_factory=list)


@runtime_checkable
class LlmArtifactGenerator(Protocol):
    """타입별 컨텍스트로 산출물 content를 생성하는 포트.

    Mermaid 또는 마크다운 텍스트만 반환한다(메타데이터/식별자 없음).
    """

    def generate(self, request: GenerationRequest) -> str: ...
