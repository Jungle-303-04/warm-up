"""산출물 생성/관리 유스케이스.

선택한 소스의 코드/문서 컨텍스트를 모아 타입별 생성기(LlmArtifactGenerator)로
산출물 content를 만들고 ArtifactStore에 저장한다. 메모(note)는 생성 없이 직접 저장한다.

외부 키 없이 동작: 생성기는 기본 결정론(Deterministic)이며, dependency는 import
파싱으로 실제 그래프를, uml/erd/change_summary는 골격을 반환한다(에러 아님).

컨텍스트 수집:
- repo 소스: repo_snapshot의 .py/.md 파일을 path와 함께 컨텍스트로.
- md/text/pdf 소스: content를 단일 컨텍스트로.
토큰 과다 방지를 위해 파일 수/총 길이에 상한을 둔다.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.notebooks.domain.artifact_ports import (
    ArtifactContext,
    ArtifactStore,
    GenerationRequest,
    LlmArtifactGenerator,
)
from app.notebooks.domain.artifact_records import ArtifactRecord, ArtifactType
from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import SourceRecord

# 컨텍스트 수집 상한(토큰 과다 방지).
MAX_CONTEXT_FILES = 40
MAX_FILE_CHARS = 4000
# dependency 외 타입에 사용하는 파일 확장자.
_CODE_EXTS = (".py",)
_DOC_EXTS = (".md", ".markdown")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class ArtifactService:
    store: NotebookStore
    artifact_store: ArtifactStore
    generator: LlmArtifactGenerator
    clock: Callable[[], datetime] = _utcnow
    id_factory: Callable[[], str] = _new_id

    def generate(
        self,
        notebook_id: str,
        *,
        type: ArtifactType,
        source_ids: list[str] | None = None,
    ) -> ArtifactRecord:
        if type == "note":
            raise ValueError("note는 generate가 아니라 create_note로 생성하세요")
        if type not in ("uml", "erd", "dependency", "change_summary"):
            raise ValueError(f"지원하지 않는 산출물 종류입니다: {type}")

        self.store.get_notebook(notebook_id)  # 존재 확인(없으면 KeyError → 404)
        sources = self.store.list_sources(notebook_id)
        selected = _select_sources(sources, source_ids)

        contexts = self._collect_contexts(selected)
        content = self.generator.generate(
            GenerationRequest(type=type, contexts=contexts)
        )

        now = self.clock()
        record = ArtifactRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            type=type,
            title=_default_title(type),
            content=content,
            source_ids=[source.id for source in selected],
            created_at=now,
            updated_at=now,
        )
        self.artifact_store.add(record)
        return record

    def create_note(
        self,
        notebook_id: str,
        *,
        content: str,
        title: str | None = None,
    ) -> ArtifactRecord:
        if content is None or not content.strip():
            raise ValueError("note는 content가 필요합니다")
        self.store.get_notebook(notebook_id)  # 존재 확인(없으면 KeyError → 404)

        now = self.clock()
        record = ArtifactRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            type="note",
            title=(title or "").strip() or "메모",
            content=content,
            source_ids=[],
            created_at=now,
            updated_at=now,
        )
        self.artifact_store.add(record)
        return record

    def list_artifacts(self, notebook_id: str) -> list[ArtifactRecord]:
        self.store.get_notebook(notebook_id)  # 존재 확인(없으면 KeyError → 404)
        return self.artifact_store.list_by_notebook(notebook_id)

    def get_artifact(self, notebook_id: str, artifact_id: str) -> ArtifactRecord:
        return self.artifact_store.get(notebook_id, artifact_id)

    def update_artifact(
        self,
        notebook_id: str,
        artifact_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
    ) -> ArtifactRecord:
        record = self.artifact_store.get(notebook_id, artifact_id)
        if title is not None:
            if not title.strip():
                raise ValueError("title은 비어 있을 수 없습니다")
            record.title = title.strip()
        if content is not None:
            record.content = content
        record.updated_at = self.clock()
        self.artifact_store.update(record)
        return record

    def delete_artifact(self, notebook_id: str, artifact_id: str) -> None:
        self.artifact_store.delete(notebook_id, artifact_id)

    # --- 내부 ---

    def _collect_contexts(
        self, sources: list[SourceRecord]
    ) -> list[ArtifactContext]:
        contexts: list[ArtifactContext] = []
        for source in sources:
            if len(contexts) >= MAX_CONTEXT_FILES:
                break
            if source.kind == "repo" and source.repo_snapshot:
                for entry in source.repo_snapshot:
                    if len(contexts) >= MAX_CONTEXT_FILES:
                        break
                    path = entry.get("path", "")
                    if not _is_relevant_path(path):
                        continue
                    contexts.append(
                        ArtifactContext(
                            source_id=source.id,
                            source_title=source.title,
                            text=(entry.get("content") or "")[:MAX_FILE_CHARS],
                            path=path,
                            language=_language_of(path),
                        )
                    )
            elif source.content:
                contexts.append(
                    ArtifactContext(
                        source_id=source.id,
                        source_title=source.title,
                        text=source.content[:MAX_FILE_CHARS],
                        path=None,
                        language=None,
                    )
                )
        return contexts


def _select_sources(
    sources: list[SourceRecord],
    source_ids: list[str] | None,
) -> list[SourceRecord]:
    if source_ids is None:
        return sources
    requested = set(source_ids)
    return [source for source in sources if source.id in requested]


def _is_relevant_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith(_CODE_EXTS) or lowered.endswith(_DOC_EXTS)


def _language_of(path: str) -> str | None:
    lowered = path.lower()
    if lowered.endswith(".py"):
        return "python"
    if lowered.endswith(_DOC_EXTS):
        return "markdown"
    return None


_TITLES: dict[ArtifactType, str] = {
    "uml": "UML 클래스 다이어그램",
    "erd": "ERD",
    "dependency": "의존성 그래프",
    "change_summary": "변경 요약",
    "note": "메모",
}


def _default_title(artifact_type: ArtifactType) -> str:
    return _TITLES.get(artifact_type, artifact_type)
