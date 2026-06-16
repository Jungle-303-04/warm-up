"""노트북 유스케이스.

노트북 CRUD와 소스 추가/조회/삭제를 담당한다. repo 소스는 RepoSyncService로
실제 저장소를 clone 해 repo_snapshot 캐시를 만든다. 트리/파일 조회는 캐시만
사용해 git 재호출 없이 처리한다. 저장은 NotebookStore 포트에만 의존한다.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from subprocess import CalledProcessError
from uuid import uuid4

from app.notebooks.domain.ports import NotebookStore
from app.notebooks.domain.records import (
    NotebookRecord,
    SourceKind,
    SourceRecord,
)
from app.pipeline.api.schemas import DEFAULT_BRANCH, PipelineRequest
from app.repository_source.infrastructure.repo_sync import RepoSyncService


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid4().hex


# content 필수 종류 / url 필수 종류
_CONTENT_KINDS = ("md", "text", "pdf")


@dataclass(slots=True)
class NotebookService:
    store: NotebookStore
    repo_sync: RepoSyncService = field(default_factory=RepoSyncService)
    clock: Callable[[], datetime] = _utcnow
    id_factory: Callable[[], str] = _new_id

    # --- 노트북 ---

    def create_notebook(self, *, title: str, summary: str | None = None) -> NotebookRecord:
        if not title or not title.strip():
            raise ValueError("title은 비어 있을 수 없습니다")
        now = self.clock()
        record = NotebookRecord(
            id=self.id_factory(),
            title=title.strip(),
            summary=summary,
            created_at=now,
            updated_at=now,
        )
        self.store.add_notebook(record)
        return record

    def get_notebook(self, notebook_id: str) -> NotebookRecord:
        return self.store.get_notebook(notebook_id)

    def list_notebooks(self) -> list[NotebookRecord]:
        # created_at 내림차순
        return sorted(
            self.store.list_notebooks(),
            key=lambda record: record.created_at,
            reverse=True,
        )

    def update_notebook(
        self,
        notebook_id: str,
        *,
        title: str | None = None,
        summary: str | None = None,
    ) -> NotebookRecord:
        record = self.store.get_notebook(notebook_id)
        if title is not None:
            if not title.strip():
                raise ValueError("title은 비어 있을 수 없습니다")
            record.title = title.strip()
        if summary is not None:
            record.summary = summary
        record.updated_at = self.clock()
        self.store.update_notebook(record)
        return record

    def delete_notebook(self, notebook_id: str) -> None:
        self.store.delete_notebook(notebook_id)

    # --- 소스 ---

    def list_sources(self, notebook_id: str) -> list[SourceRecord]:
        self.store.get_notebook(notebook_id)  # 존재 확인(없으면 KeyError)
        return self.store.list_sources(notebook_id)

    def get_source(self, notebook_id: str, source_id: str) -> SourceRecord:
        return self.store.get_source(notebook_id, source_id)

    def delete_source(self, notebook_id: str, source_id: str) -> None:
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
    ) -> SourceRecord:
        notebook = self.store.get_notebook(notebook_id)  # 없으면 KeyError → 404

        if kind in _CONTENT_KINDS:
            record = self._build_content_source(notebook_id, kind, title, content)
        elif kind == "url":
            record = self._build_url_source(notebook_id, title, url)
        elif kind == "repo":
            record = self._build_repo_source(
                notebook_id, title, repository_url, branch
            )
        else:
            raise ValueError(f"지원하지 않는 소스 종류입니다: {kind}")

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
            raise ValueError(f"{kind} 소스는 content가 필요합니다")
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind=kind,
            title=(title or "").strip() or kind,
            content=content,
            created_at=self.clock(),
        )

    def _build_url_source(
        self,
        notebook_id: str,
        title: str | None,
        url: str | None,
    ) -> SourceRecord:
        if url is None or not url.strip():
            raise ValueError("url 소스는 url이 필요합니다")
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind="url",
            title=(title or "").strip() or url,
            url=url,
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
            raise ValueError("repo 소스는 repository_url이 필요합니다")
        effective_branch = (branch or "").strip() or DEFAULT_BRANCH
        effective_title = (title or "").strip() or _repo_name_from_url(repository_url)

        try:
            snapshot = self.repo_sync.sync(
                PipelineRequest(
                    repository=effective_title,
                    repository_url=repository_url,
                    branch=effective_branch,
                )
            )
        except (ValueError, CalledProcessError) as exc:
            # clone/검증 실패는 400으로 변환되도록 ValueError로 통일
            raise ValueError(f"저장소 동기화에 실패했습니다: {exc}") from exc

        repo_snapshot = [
            {"path": file.path, "content": file.content} for file in snapshot.files
        ]
        return SourceRecord(
            id=self.id_factory(),
            notebook_id=notebook_id,
            kind="repo",
            title=effective_title,
            repository_url=repository_url,
            branch=snapshot.branch or effective_branch,
            repo_snapshot=repo_snapshot,
            created_at=self.clock(),
        )

    # --- repo 트리/파일 ---

    def get_source_tree(self, notebook_id: str, source_id: str) -> list[dict]:
        source = self.store.get_source(notebook_id, source_id)
        if source.kind != "repo" or source.repo_snapshot is None:
            raise ValueError("repo 소스에서만 트리를 조회할 수 있습니다")
        paths = [entry["path"] for entry in source.repo_snapshot]
        return build_tree(paths)

    def get_source_file(self, notebook_id: str, source_id: str, path: str) -> dict:
        source = self.store.get_source(notebook_id, source_id)
        if source.kind != "repo" or source.repo_snapshot is None:
            raise ValueError("repo 소스에서만 파일을 조회할 수 있습니다")
        for entry in source.repo_snapshot:
            if entry["path"] == path:
                return {"path": path, "content": entry["content"]}
        raise KeyError(path)


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
