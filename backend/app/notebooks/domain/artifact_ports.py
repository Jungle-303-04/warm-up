"""산출물 도메인 포트.

- ArtifactStore: 산출물 영속 저장소 추상(in-memory/SQL 어댑터가 구현).
- LlmArtifactGenerator: 타입별 컨텍스트를 받아 산출물 content(Mermaid/마크다운)를
  생성하는 추상. LangChain ChatOpenAI 어댑터와 결정론(Deterministic) 어댑터가 구현한다.
  도메인/application은 이 포트에만 의존하고 LLM 프레임워크를 직접 import 하지 않는다(DIP).

get류는 없는 id에 대해 KeyError를 던진다(API에서 404로 변환).
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.notebooks.domain.artifact_records import ArtifactRecord, ArtifactType


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
    source_url: str | None = None
    branch: str | None = None


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
