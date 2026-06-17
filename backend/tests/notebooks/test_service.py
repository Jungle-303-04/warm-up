from datetime import UTC, datetime
from itertools import count

import pytest

from app.api.errors import DomainValidationError, EntityNotFoundError
from app.notebooks.application.service import NotebookService, build_tree
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore

FIXED_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _service() -> NotebookService:
    counter = count(1)
    return NotebookService(
        store=InMemoryNotebookStore(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"id-{next(counter)}",
    )


def test_create_and_get_notebook() -> None:
    service = _service()

    notebook = service.create_notebook(title="My NB")

    fetched = service.get_notebook(notebook.id)
    assert fetched.title == "My NB"
    assert fetched.created_at == FIXED_NOW


def test_create_notebook_uses_default_title_when_blank() -> None:
    service = _service()

    notebook = service.create_notebook(title="   ")

    assert notebook.title == "새 노트북"


def test_list_notebooks_orders_by_created_at_desc() -> None:
    store = InMemoryNotebookStore()
    times = iter(
        [
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 2, 1, tzinfo=UTC),
        ]
    )
    counter = count(1)
    service = NotebookService(
        store=store,
        clock=lambda: next(times),
        id_factory=lambda: f"id-{next(counter)}",
    )

    first = service.create_notebook(title="first")
    second = service.create_notebook(title="second")

    listed = service.list_notebooks()
    assert [nb.id for nb in listed] == [second.id, first.id]


def test_update_notebook_changes_fields_and_updated_at() -> None:
    service = _service()
    notebook = service.create_notebook(title="old")

    updated = service.update_notebook(notebook.id, title="new")

    assert updated.title == "new"
    assert updated.updated_at == FIXED_NOW


def test_delete_notebook_cascades_sources() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")
    service.add_source(notebook.id, kind="md", title="doc", content="# hi")

    service.delete_notebook(notebook.id)

    with pytest.raises(EntityNotFoundError):
        service.get_notebook(notebook.id)


def test_get_unknown_notebook_raises() -> None:
    service = _service()
    with pytest.raises(EntityNotFoundError):
        service.get_notebook("nope")


def test_add_md_source_requires_content() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")

    with pytest.raises(DomainValidationError, match="content"):
        service.add_source(notebook.id, kind="md", title="doc")


def test_add_md_source_persists() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")

    source = service.add_source(
        notebook.id, kind="md", title="doc", content="# hi"
    )

    assert source.kind == "md"
    assert source.content == "# hi"
    sources = service.list_sources(notebook.id)
    assert [s.id for s in sources] == [source.id]


def test_add_url_source_requires_url() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")

    with pytest.raises(DomainValidationError, match="url"):
        service.add_source(notebook.id, kind="url", title="link")


def test_add_repo_source_uses_injected_sync() -> None:
    # 실제 git clone 없이 RepoSyncService를 가짜로 주입
    class FakeSync:
        def sync(self, request):
            from app.pipeline.router import RepoFile, RepoSnapshot

            return RepoSnapshot(
                repository=request.repository,
                branch=request.branch,
                commit_sha="abc123",
                files=[
                    RepoFile(path="src/app.py", content="print('x')"),
                    RepoFile(path="README.md", content="# readme"),
                ],
            )

    counter = count(1)
    service = NotebookService(
        store=InMemoryNotebookStore(),
        repo_sync=FakeSync(),  # type: ignore
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"id-{next(counter)}",
    )
    notebook = service.create_notebook(title="nb")

    source = service.add_source(
        notebook.id,
        kind="repo",
        repository_url="https://github.com/owner/myrepo",
    )

    assert source.kind == "repo"
    assert source.title == "myrepo"  # title 비면 URL 마지막 경로명
    assert source.branch == "main"
    assert source.repo_snapshot is not None
    assert {entry["path"] for entry in source.repo_snapshot} == {
        "src/app.py",
        "README.md",
    }


def test_repo_source_tree_and_file_lookup() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")
    # repo_snapshot 직접 주입(실제 clone 금지)
    from app.notebooks.domain.records import SourceRecord

    source = SourceRecord(
        id="src-1",
        notebook_id=notebook.id,
        kind="repo",
        title="repo",
        repository_url="https://github.com/owner/repo",
        branch="main",
        repo_snapshot=[
            {"path": "src/app.py", "content": "A"},
            {"path": "src/util/io.py", "content": "B"},
            {"path": "README.md", "content": "C"},
        ],
        created_at=FIXED_NOW,
    )
    service.store.add_source(source)

    tree = service.get_source_tree(notebook.id, "src-1")
    # dir(src) 먼저, file(README.md) 나중
    assert [n["name"] for n in tree] == ["src", "README.md"]
    src_node = tree[0]
    assert src_node["type"] == "dir"
    assert src_node["path"] == "src"
    child_names = {c["name"] for c in src_node["children"]}
    assert child_names == {"app.py", "util"}

    file = service.get_source_file(notebook.id, "src-1", "src/util/io.py")
    assert file == {"path": "src/util/io.py", "content": "B"}

    with pytest.raises(EntityNotFoundError):
        service.get_source_file(notebook.id, "src-1", "missing.py")


def test_tree_on_non_repo_source_raises() -> None:
    service = _service()
    notebook = service.create_notebook(title="nb")
    md = service.add_source(notebook.id, kind="md", title="doc", content="# hi")

    with pytest.raises(DomainValidationError, match="repo"):
        service.get_source_tree(notebook.id, md.id)


def test_build_tree_nested_structure() -> None:
    tree = build_tree(["a/b/c.py", "a/d.py", "e.txt"])

    names = [n["name"] for n in tree]
    assert names == ["a", "e.txt"]  # dir 먼저
    a = tree[0]
    assert a["type"] == "dir"
    a_children = {c["name"]: c for c in a["children"]}
    assert a_children["b"]["type"] == "dir"
    assert a_children["d.py"]["type"] == "file"
    assert a_children["b"]["children"][0]["path"] == "a/b/c.py"
