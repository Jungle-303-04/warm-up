"""산출물 생성/관리 유스케이스.

흐름:
- 선택 소스의 코드/문서 컨텍스트 수집
- 타입별 LlmArtifactGenerator 호출
- ArtifactStore 저장
- note는 생성기 없이 직접 저장

기본 생성기:
- dependency/uml/erd: 정적 파싱 기반 Mermaid
- change_summary: 코드 facts 기반 마크다운
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from app.config import Settings, get_settings
from app.notebooks.application.service import DEFAULT_OWNER_USER_ID
from app.notebooks.domain.artifact_ports import (
    ArtifactContext,
    ArtifactStore,
    GenerationRequest,
    LlmArtifactGenerator,
)
from app.notebooks.domain.artifact_records import ArtifactRecord, ArtifactType
from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import SourceRecord
from app.notebooks.domain.source_evidence import is_code_path, is_repo_document_path
from app.notebooks.domain.source_scope import select_sources

# 컨텍스트 수집 폴백 기본값
MAX_FILE_CHARS = 4000  # 파일당 본문 상한
MAX_TOTAL_CONTEXT_CHARS = 20000  # 전체 컨텍스트 예산
MAX_SELECTED_FILES = 60  # 파일 수 안전 상한
# dependency: import 그래프용 .py 파일 다수 확보
MAX_DEPENDENCY_FILES = 250
MAX_STRUCTURE_FILE_CHARS = 30_000
# dependency 외 타입용 파일 확장자
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
    store: NotebookStore
    artifact_store: ArtifactStore
    generator: LlmArtifactGenerator
    settings: Settings = field(default_factory=get_settings)
    clock: Any = field(default_factory=get_clock)
    id_factory: Any = field(default_factory=get_id_factory)

    def generate(
        self,
        notebook_id: str,
        *,
        type: ArtifactType,
        source_ids: list[str] | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> ArtifactRecord:
        if type == "note":
            raise ValueError("note는 generate가 아니라 create_note로 생성하세요")
        if type not in ("uml", "erd", "dependency", "change_summary"):
            raise ValueError(f"지원하지 않는 산출물 종류입니다: {type}")

        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        sources = self.store.list_sources(notebook_id)
        selected = select_sources(sources, source_ids)
        if source_ids is not None and not selected:
            raise ValueError("선택된 소스가 없어 산출물을 생성할 수 없습니다")
        _validate_artifact_scope(type, selected)

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
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> ArtifactRecord:
        if content is None:
            raise ValueError("note는 content가 필요합니다")
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)

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

    def list_artifacts(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> list[ArtifactRecord]:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        return self.artifact_store.list_by_notebook(notebook_id)

    def get_artifact(
        self,
        notebook_id: str,
        artifact_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> ArtifactRecord:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        return self.artifact_store.get(notebook_id, artifact_id)

    def update_artifact(
        self,
        notebook_id: str,
        artifact_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> ArtifactRecord:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
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

    def delete_artifact(
        self,
        notebook_id: str,
        artifact_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> None:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        self.artifact_store.delete(notebook_id, artifact_id)

    # --- 내부 ---

    def _collect_contexts(
        self, sources: list[SourceRecord], artifact_type: ArtifactType
    ) -> list[ArtifactContext]:
        """선택 소스 후보 수집 후 타입별 선별.

        타입별 우선순위 점수와 토큰 예산 기반.
        dependency는 import 그래프용 .py 파일 우선.
        """
        candidates: list[ArtifactContext] = []
        for source in sources:
            if artifact_type == "change_summary" and source.repo_commits:
                candidates.append(
                    ArtifactContext(
                        source_id=source.id,
                        source_title=source.title,
                        text=_format_recent_commits(source),
                        path="__recent_commits__.md",
                        language="markdown",
                        source_url=source.repository_url or source.url,
                        branch=source.branch,
                    )
                )
            if source.kind == "repo" and source.repo_snapshot:
                for entry in source.repo_snapshot:
                    path = entry.get("path", "")
                    if not _is_relevant_path(path):
                        continue
                    candidates.append(
                        ArtifactContext(
                            source_id=source.id,
                            source_title=source.title,
                            text=_slice_context_text(
                                artifact_type,
                                path,
                                entry.get("content") or "",
                                self.settings.artifact_max_file_chars,
                            ),
                            path=path,
                            language=_language_of(path),
                            source_url=source.repository_url or source.url,
                            branch=source.branch,
                        )
                    )
            elif source.content:
                candidates.append(
                    ArtifactContext(
                        source_id=source.id,
                        source_title=source.title,
                        text=source.content[:self.settings.artifact_max_file_chars],
                        path=None,
                        language=None,
                        source_url=source.repository_url or source.url,
                        branch=source.branch,
                    )
                )
        return _select_contexts(
            candidates,
            artifact_type,
            max_total_chars=self.settings.artifact_max_total_context_chars,
            max_files=self.settings.artifact_max_selected_files,
            max_dependency_files=self.settings.artifact_max_dependency_files,
        )


def _is_relevant_path(path: str) -> bool:
    lowered = path.lower()
    return lowered.endswith(_CODE_EXTS) or lowered.endswith(_DOC_EXTS)


def _select_contexts(
    candidates: list[ArtifactContext],
    artifact_type: ArtifactType,
    *,
    max_total_chars: int = MAX_TOTAL_CONTEXT_CHARS,
    max_files: int = MAX_SELECTED_FILES,
    max_dependency_files: int = MAX_DEPENDENCY_FILES,
) -> list[ArtifactContext]:
    """타입별 우선순위 기반 컨텍스트 선별.

    - dependency: .py 파일 중심
    - 그 외: 타입 점수 내림차순과 토큰 예산 기준
    """
    if artifact_type == "dependency":
        py = [c for c in candidates if c.path and c.path.lower().endswith(".py")]
        return py[:max_dependency_files]

    if artifact_type == "uml":
        structural_contexts = [
            c
            for c in sorted(
                candidates,
                key=lambda item: _relevance_score(artifact_type, item),
                reverse=True,
            )
            if _relevance_score(artifact_type, c) >= 20
        ]
        return structural_contexts[: max(max_files, 240)]

    if artifact_type == "erd":
        schema_contexts = [
            c
            for c in sorted(
                candidates,
                key=lambda item: _relevance_score(artifact_type, item),
                reverse=True,
            )
            if _relevance_score(artifact_type, c) >= 20
        ]
        return schema_contexts[: max(max_files, 240)]

    ranked = sorted(
        candidates,
        key=lambda c: _relevance_score(artifact_type, c),
        reverse=True,
    )
    selected: list[ArtifactContext] = []
    used = 0
    for ctx in ranked:
        if len(selected) >= max_files or used >= max_total_chars:
            break
        # 관련도 0 이하 파일 제외
        if _relevance_score(artifact_type, ctx) <= 0 and selected:
            break
        selected.append(ctx)
        used += len(ctx.text)
    return selected


def _validate_artifact_scope(artifact_type: ArtifactType, sources: list[SourceRecord]) -> None:
    """UML/ERD 단일 저장소 scope 검증.

    여러 repo 병합 시 클래스/테이블 이름 충돌 가능.
    비-repo 문서/SQL만 선택한 경우는 허용.
    """

    if artifact_type not in {"uml", "erd"}:
        return
    repo_sources = [source for source in sources if source.kind == "repo"]
    if len(repo_sources) <= 1:
        return
    labels = ", ".join(_source_scope_label(source) for source in repo_sources[:4])
    if len(repo_sources) > 4:
        labels += f" 외 {len(repo_sources) - 4}개"
    raise ValueError(
        f"{_default_title(artifact_type)}은 저장소 하나를 기준으로 생성해 주세요. "
        f"현재 선택된 저장소: {labels}"
    )


def _source_scope_label(source: SourceRecord) -> str:
    branch = f" / {source.branch}" if source.branch else ""
    return f"{source.title}{branch}"


def _relevance_score(artifact_type: ArtifactType, ctx: ArtifactContext) -> int:
    """산출물 타입별 파일 관련도 점수."""
    path = (ctx.path or "").lower()
    text = ctx.text
    score = 1  # 관련 파일 최소 점수
    is_doc_path = is_repo_document_path(path)
    is_code_file = is_code_path(path) and not is_doc_path

    if artifact_type == "uml":
        if is_code_file:
            score += 20
        if is_doc_path:
            score -= 10
        score += text.count("class ") * 5
        score += (text.count("interface ") + text.count("def ")) * 1
        if _has_any(path, ("domain", "record", "model", "entity", "service", "schema")):
            score += 20
    elif artifact_type == "erd":
        if is_code_file:
            score += 20
        if is_doc_path:
            score -= 10
        if path.endswith(".sql"):
            score += 100
        score += (text.count("Column(") + text.count("mapped_column(")) * 8
        score += text.count("ForeignKey(") * 12
        score += text.count("__tablename__") * 30
        if _has_any(path, ("model", "schema", "entity", "table", "orm", "migration")):
            score += 25
    elif artifact_type == "change_summary":
        if path == "__recent_commits__.md":
            score += 1000
        if is_code_file:
            score += 35
        if path.endswith(".sql"):
            score += 35
        if _has_any(
            path,
            (
                "app/",
                "src/",
                "backend/",
                "frontend/",
                "api",
                "router",
                "route",
                "service",
                "domain",
                "model",
                "schema",
                "store",
                "migration",
                "config",
            ),
        ):
            score += 20
        score += text.count("class ") * 3
        score += text.count("def ") * 2
        score += text.count("function ") * 2
        score += text.count("export ") * 2
        if is_doc_path:
            score -= 12
        if _has_any(path, ("readme", "changelog", "changes", "history")):
            score += 5

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


def _format_recent_commits(source: SourceRecord, limit: int = 8) -> str:
    lines = [f"# 최근 커밋: {source.title}"]
    for commit in (source.repo_commits or [])[:limit]:
        short_sha = str(commit.get("short_sha") or commit.get("sha") or "")[:12]
        message = str(commit.get("message") or "(메시지 없음)").strip()
        author = str(commit.get("author_name") or "unknown")
        authored_at = str(commit.get("authored_at") or "date unknown")
        commit_label = f"`{short_sha}`"
        if commit.get("html_url"):
            commit_label = f"[{commit_label}]({commit['html_url']})"
        lines.append(f"- {commit_label} {authored_at} {author}: {message}")
        for file in _commit_files(commit)[:8]:
            path = file["path"]
            status = file["status"]
            link = _repo_file_link(source, path)
            label = f"[`{path}`]({link})" if link else f"`{path}`"
            lines.append(f"  - {status} {label}")
    return "\n".join(lines)


def _commit_files(commit: dict) -> list[dict[str, str]]:
    raw_files = commit.get("files")
    if not isinstance(raw_files, list):
        return []
    files: list[dict[str, str]] = []
    for item in raw_files:
        if not isinstance(item, dict):
            continue
        path = item.get("path") or item.get("filename")
        if not isinstance(path, str) or not path:
            continue
        files.append({"path": path, "status": str(item.get("status") or "modified")})
    return files


def _repo_file_link(source: SourceRecord, path: str) -> str | None:
    if not source.repository_url or "github.com" not in source.repository_url:
        return None
    repo_url = source.repository_url.removesuffix(".git").rstrip("/")
    branch = quote(source.branch or "main", safe="/")
    quoted_path = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"{repo_url}/blob/{branch}/{quoted_path}"


def _slice_context_text(
    artifact_type: ArtifactType,
    path: str,
    content: str,
    default_limit: int,
) -> str:
    lowered = path.lower()
    if artifact_type == "erd" and (
        lowered.endswith(".sql")
        or _has_any(lowered, ("model", "schema", "entity", "table", "migration", "orm"))
    ):
        return content[: max(default_limit, MAX_STRUCTURE_FILE_CHARS)]
    if artifact_type == "uml" and _has_any(
        lowered,
        ("api", "router", "service", "domain", "model", "entity", "schema", "store", "agent"),
    ):
        return content[: max(default_limit, MAX_STRUCTURE_FILE_CHARS)]
    return content[:default_limit]


_TITLES: dict[ArtifactType, str] = {
    "uml": "UML 클래스 다이어그램",
    "erd": "ERD",
    "dependency": "의존성 그래프",
    "change_summary": "변경 요약",
    "note": "메모",
}


def _default_title(artifact_type: ArtifactType) -> str:
    return _TITLES.get(artifact_type, artifact_type)
