import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.main import app
from app.notebooks.dependencies import _in_memory_chunk_store as _chunk_store
from app.notebooks.dependencies import _in_memory_store as _store

client = TestClient(app)


def _claims(user_id: int, login: str = "t") -> SessionClaims:
    return SessionClaims(user_id=user_id, login=login)


@pytest.fixture(autouse=True)
def _reset_store():
    app.dependency_overrides[get_current_claims] = lambda: _claims(1)
    _store.cache_clear()
    _chunk_store.cache_clear()
    yield
    app.dependency_overrides.clear()
    _store.cache_clear()
    _chunk_store.cache_clear()


def _create_notebook(title: str = "My NB") -> dict:
    response = client.post("/notebooks", json={"title": title})
    assert response.status_code == 201
    return response.json()


def test_create_notebook_returns_view() -> None:
    body = _create_notebook()

    assert body["title"] == "My NB"
    assert "summary" not in body
    assert body["source_count"] == 0
    assert "id" in body


def test_list_notebooks_orders_desc() -> None:
    first = _create_notebook(title="first")
    second = _create_notebook(title="second")

    listed = client.get("/notebooks").json()["notebooks"]
    ids = [nb["id"] for nb in listed]
    assert ids[0] == second["id"]
    assert ids[1] == first["id"]


def test_notebooks_are_scoped_by_authenticated_user() -> None:
    first_user_notebook = _create_notebook(title="private")

    app.dependency_overrides[get_current_claims] = lambda: _claims(2, "other")

    listed = client.get("/notebooks")
    assert listed.status_code == 200
    assert listed.json()["notebooks"] == []
    assert client.get(f"/notebooks/{first_user_notebook['id']}").status_code == 404
    assert client.get(
        f"/notebooks/{first_user_notebook['id']}/sources"
    ).status_code == 404
    assert client.get(
        f"/notebooks/{first_user_notebook['id']}/chat/messages"
    ).status_code == 404
    assert client.get(
        f"/notebooks/{first_user_notebook['id']}/artifacts"
    ).status_code == 404


def test_get_notebook_detail_includes_sources() -> None:
    nb = _create_notebook()
    client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "md", "title": "doc", "content": "# hi"},
    )

    detail = client.get(f"/notebooks/{nb['id']}").json()
    assert detail["source_count"] == 1
    assert detail["sources"][0]["kind"] == "md"
    # content는 SourceView에 없어야 함
    assert "content" not in detail["sources"][0]


def test_patch_notebook_updates_fields() -> None:
    nb = _create_notebook()

    updated = client.patch(
        f"/notebooks/{nb['id']}", json={"title": "renamed"}
    ).json()
    assert updated["title"] == "renamed"


def test_delete_notebook_returns_204_and_cascades() -> None:
    nb = _create_notebook()
    client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "text", "title": "t", "content": "x"},
    )

    deleted = client.delete(f"/notebooks/{nb['id']}")
    assert deleted.status_code == 204

    assert client.get(f"/notebooks/{nb['id']}").status_code == 404


def test_get_unknown_notebook_returns_404() -> None:
    assert client.get("/notebooks/nope").status_code == 404


def test_create_md_source_requires_content_returns_400() -> None:
    nb = _create_notebook()

    response = client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "md", "title": "doc"},
    )
    assert response.status_code == 400


def test_source_detail_includes_content() -> None:
    nb = _create_notebook()
    created = client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "md", "title": "doc", "content": "# hi"},
    ).json()

    detail = client.get(
        f"/notebooks/{nb['id']}/sources/{created['id']}"
    ).json()
    assert detail["content"] == "# hi"


def test_tree_endpoint_rejects_non_repo_source() -> None:
    nb = _create_notebook()
    created = client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "md", "title": "doc", "content": "# hi"},
    ).json()

    response = client.get(
        f"/notebooks/{nb['id']}/sources/{created['id']}/tree"
    )
    assert response.status_code == 400


def test_delete_source_returns_204() -> None:
    nb = _create_notebook()
    created = client.post(
        f"/notebooks/{nb['id']}/sources",
        json={"kind": "url", "title": "link", "url": "https://example.com"},
    ).json()

    deleted = client.delete(f"/notebooks/{nb['id']}/sources/{created['id']}")
    assert deleted.status_code == 204
    assert (
        client.get(f"/notebooks/{nb['id']}/sources/{created['id']}").status_code == 404
    )


def test_chat_endpoint_returns_answer_with_citations() -> None:
    nb = _create_notebook()
    source = client.post(
        f"/notebooks/{nb['id']}/sources",
        json={
            "kind": "md",
            "title": "auth.md",
            "content": "인증 미들웨어는 JWT 만료 시간을 확인하고 401 응답을 반환한다.",
        },
    ).json()

    response = client.post(
        f"/notebooks/{nb['id']}/chat",
        json={"question": "JWT 만료는 어디서 확인하나요?", "source_ids": [source["id"]]},
    )

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert body["citations"][0]["source_id"] == source["id"]
    assert body["citations"][0]["source_title"] == "auth.md"
    assert "JWT" in body["citations"][0]["snippet"]

    history = client.get(f"/notebooks/{nb['id']}/chat/messages")
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "JWT 만료는 어디서 확인하나요?"
    assert messages[0]["source_ids"] == [source["id"]]
    assert messages[1]["content"] == body["answer"]
    assert messages[1]["citations"][0]["source_id"] == source["id"]


def test_chat_endpoint_returns_grounding_gap_without_sources() -> None:
    nb = _create_notebook()

    response = client.post(
        f"/notebooks/{nb['id']}/chat",
        json={"question": "무엇을 담고 있나요?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == []
    assert "소스" in body["answer"]
