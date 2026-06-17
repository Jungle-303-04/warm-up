"""ArtifactService 유스케이스 테스트(in-memory, LLM 키 없음).

- dependency: repo 소스의 import 파싱으로 결정론 Mermaid 생성.
- uml/erd: 키 없을 때 골격 폴백(에러 없음).
- note: 생성/조회/수정/삭제 CRUD.
"""

from datetime import UTC, datetime
from itertools import count

import pytest

from app.notebooks.application.artifact_service import ArtifactService
from app.notebooks.domain.records import SourceRecord
from app.notebooks.infrastructure.artifact_generators import (
    DeterministicArtifactGenerator,
)
from app.notebooks.infrastructure.in_memory_artifact_store import InMemoryArtifactStore
from app.notebooks.infrastructure.in_memory_store import InMemoryNotebookStore
from app.api.errors import EntityNotFoundError

FIXED_NOW = datetime(2026, 6, 17, 12, 0, tzinfo=UTC)


def _service() -> tuple[ArtifactService, InMemoryNotebookStore]:
    store = InMemoryNotebookStore()
    counter = count(1)
    service = ArtifactService(
        store=store,
        artifact_store=InMemoryArtifactStore(),
        generator=DeterministicArtifactGenerator(),
        clock=lambda: FIXED_NOW,
        id_factory=lambda: f"art-{next(counter)}",
    )
    return service, store


def _notebook_with_repo(store: InMemoryNotebookStore) -> str:
    from app.notebooks.domain.records import NotebookRecord

    store.add_notebook(
        NotebookRecord(
            id="nb-1",
            title="nb",
            summary=None,
            created_at=FIXED_NOW,
            updated_at=FIXED_NOW,
        )
    )
    store.add_source(
        SourceRecord(
            id="src-1",
            notebook_id="nb-1",
            kind="repo",
            title="repo",
            created_at=FIXED_NOW,
            repo_snapshot=[
                {"path": "app/main.py", "content": "from app.core import run\n"},
                {"path": "app/core.py", "content": "import os\n"},
            ],
        )
    )
    return "nb-1"


def _notebook_only(store: InMemoryNotebookStore) -> str:
    from app.notebooks.domain.records import NotebookRecord

    store.add_notebook(
        NotebookRecord(
            id="nb-1",
            title="nb",
            summary=None,
            created_at=FIXED_NOW,
            updated_at=FIXED_NOW,
        )
    )
    return "nb-1"


def test_generate_dependency_from_repo_imports() -> None:
    service, store = _service()
    nb_id = _notebook_with_repo(store)

    record = service.generate(nb_id, type="dependency", source_ids=["src-1"])

    assert record.type == "dependency"
    assert record.content.startswith("flowchart LR")
    assert "app.main" in record.content and "app.core" in record.content
    assert record.content.count("-->") == 1  # main -> core
    assert record.source_ids == ["src-1"]
    # 저장도 됐는지 확인
    assert service.get_artifact(nb_id, record.id).id == record.id


def test_generate_uml_without_key_returns_skeleton() -> None:
    service, store = _service()
    nb_id = _notebook_with_repo(store)

    record = service.generate(nb_id, type="uml", source_ids=["src-1"])

    assert record.type == "uml"
    assert record.content.startswith("classDiagram")
    assert "LLM 키가 필요합니다" in record.content


def test_generate_erd_without_key_returns_skeleton() -> None:
    service, store = _service()
    nb_id = _notebook_with_repo(store)

    record = service.generate(nb_id, type="erd", source_ids=None)

    assert record.type == "erd"
    assert record.content.startswith("erDiagram")


def test_generate_unknown_notebook_raises_keyerror() -> None:
    service, _ = _service()
    with pytest.raises(EntityNotFoundError):
        service.generate("missing", type="dependency")


def test_note_crud() -> None:
    service, store = _service()
    nb_id = _notebook_only(store)

    created = service.create_note(nb_id, content="첫 메모", title="제목")
    assert created.type == "note"
    assert created.title == "제목"
    assert created.content == "첫 메모"
    assert created.source_ids == []

    fetched = service.get_artifact(nb_id, created.id)
    assert fetched.content == "첫 메모"

    updated = service.update_artifact(
        nb_id, created.id, title="새 제목", content="수정됨"
    )
    assert updated.title == "새 제목"
    assert updated.content == "수정됨"

    listed = service.list_artifacts(nb_id)
    assert [a.id for a in listed] == [created.id]

    service.delete_artifact(nb_id, created.id)
    assert service.list_artifacts(nb_id) == []
    with pytest.raises(EntityNotFoundError):
        service.get_artifact(nb_id, created.id)


def test_create_note_requires_content() -> None:
    service, store = _service()
    nb_id = _notebook_only(store)
    with pytest.raises(ValueError, match="content"):
        service.create_note(nb_id, content=None)
