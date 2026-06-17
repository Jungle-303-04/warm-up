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
from fastapi import Depends
from app.notebooks.dependencies import get_notebook_store, get_artifact_store, get_artifact_generator

# 컨텍스트 수집 상한.
MAX_FILE_CHARS = 4000  # 파일당 본문 상한
# 비-dependency 타입: 점수 상위 파일을 토큰 예산까지 담는다(파일 수 대신 총량 기준).
MAX_TOTAL_CONTEXT_CHARS = 20000  # 전체 컨텍스트 예산(상위 관련 파일 우선)
MAX_SELECTED_FILES = 60  # 안전 상한(파일 수)
# dependency: import 그래프 정확도를 위해 가능한 한 많은 .py를 담는다(상단 import만 파싱).
MAX_DEPENDENCY_FILES = 250
# dependency 외 타입에 사용하는 파일 확장자.
_CODE_EXTS = (
    ".py", ".ts", ".tsx", ".js", ".jsx", ".sql", 
    ".go", ".rs", ".java", ".json", ".yaml", ".yml", 
    ".toml", ".h", ".cpp", ".cc", ".cs", ".html", ".css"
)
_DOC_EXTS = (".md", ".markdown")


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


def get_id_factory() -> Callable[[], str]:
    return lambda: uuid4().hex


@dataclass
class ArtifactService:
    store: NotebookStore = Depends(get_notebook_store)
    artifact_store: ArtifactStore = Depends(get_artifact_store)
    generator: LlmArtifactGenerator = Depends(get_artifact_generator)
    clock: Callable[[], datetime] = Depends(get_clock)
    id_factory: Callable[[], str] = Depends(get_id_factory)

    def __post_init__(self) -> None:
        from fastapi.params import Depends as DependsClass
        if isinstance(self.clock, DependsClass):
            self.clock = self.clock.dependency()
        if isinstance(self.id_factory, DependsClass):
            self.id_factory = self.id_factory.dependency()

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

        contexts = self._collect_contexts(selected, type)
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
        content: str | None,
        title: str | None = None,
    ) -> ArtifactRecord:
        if content is None:
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
        self, sources: list[SourceRecord], artifact_type: ArtifactType
    ) -> list[ArtifactContext]:
        """선택 소스에서 후보를 모은 뒤 타입에 맞게 선별한다.

        "처음 N개"가 아니라 타입별 우선순위 점수로 정렬해 토큰 예산까지 담는다.
        파일 수가 많아도(예: 4000개) 산출물 종류에 관련된 파일이 먼저 들어간다.
        dependency는 import 그래프 정확도를 위해 가능한 한 많은 .py를 담는다.
        """
        candidates: list[ArtifactContext] = []
        for source in sources:
            if source.kind == "repo" and source.repo_snapshot:
                for entry in source.repo_snapshot:
                    path = entry.get("path", "")
                    if not _is_relevant_path(path):
                        continue
                    candidates.append(
                        ArtifactContext(
                            source_id=source.id,
                            source_title=source.title,
                            text=(entry.get("content") or "")[:MAX_FILE_CHARS],
                            path=path,
                            language=_language_of(path),
                        )
                    )
            elif source.content:
                candidates.append(
                    ArtifactContext(
                        source_id=source.id,
                        source_title=source.title,
                        text=source.content[:MAX_FILE_CHARS],
                        path=None,
                        language=None,
                    )
                )
        return _select_contexts(candidates, artifact_type)


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


def _select_contexts(
    candidates: list[ArtifactContext], artifact_type: ArtifactType
) -> list[ArtifactContext]:
    """타입별 우선순위로 컨텍스트를 선별한다.

    - dependency: import 그래프용으로 .py 파일을 가능한 한 많이(MAX_DEPENDENCY_FILES).
    - 그 외: 타입 점수 내림차순으로 정렬해 토큰 예산(MAX_TOTAL_CONTEXT_CHARS)까지 담는다.
    """
    if artifact_type == "dependency":
        py = [c for c in candidates if c.path and c.path.lower().endswith(".py")]
        return py[:MAX_DEPENDENCY_FILES]

    ranked = sorted(
        candidates,
        key=lambda c: _relevance_score(artifact_type, c),
        reverse=True,
    )
    selected: list[ArtifactContext] = []
    used = 0
    for ctx in ranked:
        if len(selected) >= MAX_SELECTED_FILES or used >= MAX_TOTAL_CONTEXT_CHARS:
            break
        # 관련도 0 이하(점수가 음수)인 파일까지 굳이 채우지 않는다.
        if _relevance_score(artifact_type, ctx) <= 0 and selected:
            break
        selected.append(ctx)
        used += len(ctx.text)
    return selected


def _relevance_score(artifact_type: ArtifactType, ctx: ArtifactContext) -> int:
    """산출물 타입별 파일 관련도 점수(높을수록 먼저 담는다)."""
    path = (ctx.path or "").lower()
    text = ctx.text
    score = 1  # 기본(관련 파일은 최소 1점)

    if artifact_type == "uml":
        score += text.count("class ") * 5
        score += (text.count("interface ") + text.count("def ")) * 1
        if _has_any(path, ("domain", "record", "model", "entity", "service", "schema")):
            score += 20
    elif artifact_type == "erd":
        if path.endswith(".sql"):
            score += 100
        score += (text.count("Column(") + text.count("mapped_column(")) * 8
        score += text.count("ForeignKey(") * 12
        score += text.count("__tablename__") * 30
        if _has_any(path, ("model", "schema", "entity", "table", "orm", "migration")):
            score += 25
    elif artifact_type == "change_summary":
        if path.endswith(_DOC_EXTS):
            score += 30
        if _has_any(path, ("readme", "changelog", "changes", "history")):
            score += 40
        score += text.count("class ") + text.count("def ")

    if "test" in path or path.endswith((".min.js", ".lock")):
        score -= 15
    return score


def _has_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(n in haystack for n in needles)


def _language_of(path: str) -> str | None:
    lowered = path.lower()
    if lowered.endswith(".py"):
        return "python"
    if lowered.endswith((".ts", ".tsx")):
        return "typescript"
    if lowered.endswith((".js", ".jsx")):
        return "javascript"
    if lowered.endswith(".sql"):
        return "sql"
    if lowered.endswith((".yaml", ".yml")):
        return "yaml"
    if lowered.endswith(".json"):
        return "json"
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
