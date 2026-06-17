"""산출물 엔드포인트 통합 테스트(TestClient, in-memory, LLM 키 없음).

네트워크/실제 LLM 호출 없음. dependency 결정론 생성, note CRUD, uml/erd 골격 폴백을 검증한다.
"""

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.config import Settings, get_settings
from app.main import app
from app.notebooks.dependencies import _in_memory_artifact_store as _artifact_store
from app.notebooks.dependencies import _in_memory_chunk_store as _chunk_store
from app.notebooks.dependencies import _in_memory_store as _store

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_store():
    app.dependency_overrides[get_current_claims] = lambda: SessionClaims(user_id=1, login="t")
    app.dependency_overrides[get_settings] = lambda: Settings(
        openai_api_key="",
        llm_provider="openai",
        postgres_database_url=None,
    )
    _store.cache_clear()
    _chunk_store.cache_clear()
    _artifact_store.cache_clear()
    yield
    app.dependency_overrides.clear()
    _store.cache_clear()
    _chunk_store.cache_clear()
    _artifact_store.cache_clear()


def _create_notebook() -> str:
    response = client.post("/notebooks", json={"title": "NB"})
    assert response.status_code == 201
    return response.json()["id"]


def _add_repo_source(notebook_id: str) -> str:
    # repo clone 없이 md/text 본문만으로는 dependency 그래프가 비므로,
    # 본 테스트는 md 소스로 골격/요약 폴백을, dependency 그래프는 service 테스트가 담당.
    response = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "text", "title": "code", "content": "print('hi')"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_generate_dependency_returns_mermaid_flowchart() -> None:
    nb = _create_notebook()
    _add_repo_source(nb)  # path 없는 text 소스 → 그래프는 비지만 에러 없이 flowchart 반환

    response = client.post(
        f"/notebooks/{nb}/artifacts", json={"type": "dependency"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "dependency"
    assert body["content"].startswith("flowchart LR")
    # ArtifactView 필드 전부 존재
    for key in (
        "id",
        "notebook_id",
        "type",
        "title",
        "content",
        "source_ids",
        "created_at",
        "updated_at",
    ):
        assert key in body


def test_generate_uml_without_key_returns_skeleton() -> None:
    nb = _create_notebook()

    response = client.post(f"/notebooks/{nb}/artifacts", json={"type": "uml"})
    assert response.status_code == 201
    body = response.json()
    assert body["content"].startswith("classDiagram")
    assert "LLM 키가 필요합니다" in body["content"]


def test_generate_erd_without_key_returns_skeleton() -> None:
    nb = _create_notebook()

    response = client.post(f"/notebooks/{nb}/artifacts", json={"type": "erd"})
    assert response.status_code == 201
    assert response.json()["content"].startswith("erDiagram")


def test_generate_on_missing_notebook_returns_404() -> None:
    response = client.post("/notebooks/missing/artifacts", json={"type": "uml"})
    assert response.status_code == 404


def test_note_crud_endpoints() -> None:
    nb = _create_notebook()

    # 생성
    created = client.post(
        f"/notebooks/{nb}/artifacts/note",
        json={"title": "메모1", "content": "내용"},
    )
    assert created.status_code == 201
    art = created.json()
    assert art["type"] == "note"
    assert art["title"] == "메모1"
    assert art["source_ids"] == []
    aid = art["id"]

    # 조회(단건)
    got = client.get(f"/notebooks/{nb}/artifacts/{aid}")
    assert got.status_code == 200
    assert got.json()["content"] == "내용"

    # 목록
    listed = client.get(f"/notebooks/{nb}/artifacts")
    assert listed.status_code == 200
    ids = [a["id"] for a in listed.json()["artifacts"]]
    assert aid in ids

    # 수정
    patched = client.patch(
        f"/notebooks/{nb}/artifacts/{aid}",
        json={"title": "메모2", "content": "새 내용"},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "메모2"
    assert patched.json()["content"] == "새 내용"

    # 삭제
    deleted = client.delete(f"/notebooks/{nb}/artifacts/{aid}")
    assert deleted.status_code == 204
    assert client.get(f"/notebooks/{nb}/artifacts/{aid}").status_code == 404


def test_create_note_requires_content_returns_400() -> None:
    nb = _create_notebook()
    response = client.post(
        f"/notebooks/{nb}/artifacts/note", json={"content": None}
    )
    assert response.status_code == 400
