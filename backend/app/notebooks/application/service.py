"""노트북 유스케이스.

노트북 CRUD와 소스 추가/조회/삭제를 담당한다. repo 소스 추가는 사용자 입력을
검증해 메타데이터만 즉시 저장하고, 실제 clone 및 repo_snapshot 갱신은
IndexingService가 백그라운드 진행 상태로 처리한다. 트리/파일 조회는 캐시만
사용해 git 재호출 없이 처리한다. 저장은 NotebookStore 포트에만 의존한다.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.api.errors import DomainValidationError, EntityNotFoundError
from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import (
    NotebookRecord,
    SourceKind,
    SourceRecord,
)
from app.pipeline.router import DEFAULT_BRANCH
from app.repo_rag.domain.identity import hash_text


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


def get_id_factory() -> Callable[[], str]:
    return lambda: uuid4().hex


# content 필수 종류 / url 필수 종류
_CONTENT_KINDS = ("md", "text", "pdf")
DEFAULT_OWNER_USER_ID = 0
DEFAULT_NOTEBOOK_TITLE = "새 노트북"


@dataclass
class NotebookService:
    store: NotebookStore
    clock: Any = field(default_factory=get_clock)
    id_factory: Any = field(default_factory=get_id_factory)

    # --- 노트북 ---

    def create_notebook(
        self,
        *,
        title: str | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> NotebookRecord:
        effective_title = (title or "").strip() or DEFAULT_NOTEBOOK_TITLE
        now = self.clock()
        record = NotebookRecord(
            id=self.id_factory(),
            owner_user_id=owner_user_id,
            title=effective_title,
            created_at=now,
            updated_at=now,
            sources=[],
        )
        self.store.add_notebook(record)
        return record

    def get_notebook(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> NotebookRecord:
        record = self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        record.sources = self.store.list_sources(notebook_id)
        return record

    def list_notebooks(
        self,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> list[NotebookRecord]:
        # created_at 내림차순
        records = self.store.list_notebooks(owner_user_id=owner_user_id)
        for r in records:
            r.sources = self.store.list_sources(r.id)
        return sorted(
            records,
            key=lambda record: record.created_at,
            reverse=True,
        )

    def update_notebook(
        self,
        notebook_id: str,
        *,
        title: str | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> NotebookRecord:
        record = self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        if title is not None:
            if not title.strip():
                raise DomainValidationError("title은 비어 있을 수 없습니다")
            record.title = title.strip()
        record.updated_at = self.clock()
        self.store.update_notebook(record)
        record.sources = self.store.list_sources(notebook_id)
        return record

    def delete_notebook(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> None:
        self.store.delete_notebook(notebook_id, owner_user_id=owner_user_id)

    # --- 소스 ---

    def list_sources(
        self,
        notebook_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> list[SourceRecord]:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        return self.store.list_sources(notebook_id)

    def get_source(
        self,
        notebook_id: str,
        source_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> SourceRecord:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        return self.store.get_source(notebook_id, source_id)

    def delete_source(
        self,
        notebook_id: str,
        source_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> None:
        self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)
        self.store.delete_source(notebook_id, source_id)

    def add_source(
        self,
        notebook_id: str,
        *,
        kind: SourceKind,
        title: str | None = None,
        content: str | None = None,
        url: str | None = None,
        repository_url: str | None = None,
        branch: str | None = None,
        derived_from_artifact_id: str | None = None,
        lineage_source_ids: list[str] | None = None,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> SourceRecord:
        notebook = self.store.get_notebook(notebook_id, owner_user_id=owner_user_id)

        if kind in _CONTENT_KINDS:
            record = self._build_content_source(notebook_id, kind, title, content)
        elif kind == "url":
            record = self._build_url_source(notebook_id, title, url)
        elif kind == "repo":
            record = self._build_repo_source(
                notebook_id, title, repository_url, branch
            )
        else:
            raise DomainValidationError(f"지원하지 않는 소스 종류입니다: {kind}")

        record.derived_from_artifact_id = derived_from_artifact_id
        record.lineage_source_ids = lineage_source_ids

        self.store.add_source(record)
        # 소스 추가는 노트북 변경으로 간주 → updated_at 갱신
        notebook.updated_at = self.clock()
        self.store.update_notebook(notebook)
        return record

    def _build_content_source(
        self,
        notebook_id: str,
        kind: SourceKind,
        title: str | None,
        content: str | None,
    ) -> SourceRecord:
        if content is None or not content.strip():
            raise DomainValidationError(f"{kind} 소스는 content가 필요합니다")
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind=kind,
            title=(title or "").strip() or kind,
            content=content,
            content_hash=hash_text(content),
            created_at=self.clock(),
        )

    def _build_url_source(
        self,
        notebook_id: str,
        title: str | None,
        url: str | None,
    ) -> SourceRecord:
        if url is None or not url.strip():
            raise DomainValidationError("url 소스는 url이 필요합니다")
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind="url",
            title=(title or "").strip() or url,
            url=url,
            content_hash=hash_text(url.strip()),
            created_at=self.clock(),
        )

    def _build_repo_source(
        self,
        notebook_id: str,
        title: str | None,
        repository_url: str | None,
        branch: str | None,
    ) -> SourceRecord:
        if repository_url is None or not repository_url.strip():
            raise DomainValidationError("repo 소스는 repository_url이 필요합니다")
        effective_branch = (branch or "").strip() or DEFAULT_BRANCH
        effective_title = (title or "").strip() or _repo_name_from_url(repository_url)

        normalized_url = repository_url.strip()
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind="repo",
            title=effective_title,
            repository_url=normalized_url,
            branch=effective_branch,
            # 실제 파일 스냅샷 hash는 백그라운드 인덱싱에서 clone 성공 후 갱신됨
            content_hash=hash_text(f"{normalized_url}@{effective_branch}"),
            created_at=self.clock(),
        )

    # --- repo 트리/파일 ---

    def get_source_tree(
        self,
        notebook_id: str,
        source_id: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> list[dict]:
        source = self.get_source(notebook_id, source_id, owner_user_id=owner_user_id)
        if source.kind != "repo":
            raise DomainValidationError("repo 소스에서만 트리를 조회할 수 있습니다")
        if source.repo_snapshot is None:
            raise DomainValidationError("저장소 분석이 아직 완료되지 않았습니다")
        paths = [entry["path"] for entry in source.repo_snapshot]
        return build_tree(paths)

    def get_source_file(
        self,
        notebook_id: str,
        source_id: str,
        path: str,
        *,
        owner_user_id: int = DEFAULT_OWNER_USER_ID,
    ) -> dict:
        source = self.get_source(notebook_id, source_id, owner_user_id=owner_user_id)
        if source.kind != "repo":
            raise DomainValidationError("repo 소스에서만 파일을 조회할 수 있습니다")
        if source.repo_snapshot is None:
            raise DomainValidationError("저장소 분석이 아직 완료되지 않았습니다")
        for entry in source.repo_snapshot:
            if entry["path"] == path:
                return {"path": path, "content": entry["content"]}
        raise EntityNotFoundError(path)


def _repo_name_from_url(repository_url: str) -> str:
    value = repository_url.strip().rstrip("/").removesuffix(".git")
    name = value.split("/")[-1] if value else ""
    return name or "repository"


def build_tree(paths: list[str]) -> list[dict]:
    """path 목록을 중첩 디렉터리 트리로 변환한다.

    각 노드: {name, path, type:"dir"|"file", children?}.
    디렉터리는 children을 가지며, dir 먼저/이름 오름차순으로 정렬한다.
    """
    root: dict = {}

    for raw_path in paths:
        parts = [part for part in raw_path.split("/") if part]
        if not parts:
            continue
        cursor = root
        accumulated: list[str] = []
        for index, part in enumerate(parts):
            accumulated.append(part)
            is_file = index == len(parts) - 1
            node = cursor.get(part)
            if node is None:
                node = {
                    "name": part,
                    "path": "/".join(accumulated),
                    "type": "file" if is_file else "dir",
                    "_children": {},
                }
                cursor[part] = node
            if not is_file:
                node["type"] = "dir"
                cursor = node["_children"]

    return _finalize(root)


def _finalize(level: dict) -> list[dict]:
    nodes: list[dict] = []
    for node in level.values():
        children = node.pop("_children", {})
        if node["type"] == "dir":
            node["children"] = _finalize(children)
        nodes.append(node)
    # 디렉터리 먼저, 그다음 이름 오름차순
    nodes.sort(key=lambda item: (item["type"] != "dir", item["name"]))
    return nodes
