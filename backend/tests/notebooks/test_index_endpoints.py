"""인덱싱/SSE 엔드포인트 테스트.

get_current_claims를 override해 인증을 우회하고, 소스 생성 시 BackgroundTasks가
인덱싱을 수행한 뒤 진행 상태/SSE를 조회한다. in-memory + deterministic 경로.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.main import app
from app.notebooks.dependencies import (
    _in_memory_chunk_store as _chunk_store,
)
from app.notebooks.dependencies import (
    _in_memory_store as _store,
)
from app.notebooks.domain.indexing_progress import get_progress_registry


@pytest.fixture(autouse=True)
def _setup():
    app.dependency_overrides[get_current_claims] = lambda: SessionClaims(user_id=1, login="t")
    _store.cache_clear()
    _chunk_store.cache_clear()
    yield
    app.dependency_overrides.clear()
    _store.cache_clear()
    _chunk_store.cache_clear()


# TestClient는 BackgroundTasks를 응답 후 동기 실행하므로, 응답을 받으면
# 인덱싱이 이미 완료된 상태가 된다.
client = TestClient(app)


def _create_notebook() -> str:
    response = client.post("/notebooks", json={"title": "nb"})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_source_triggers_indexing_and_progress_reports_done() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "md", "title": "a.md", "content": "# t\n\n세션 토큰 만료 검증"},
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    progress = client.get(f"/notebooks/{notebook_id}/sources/{source_id}/index")
    assert progress.status_code == 200
    body = progress.json()
    assert body["status"] == "done"
    assert body["percent"] == 100
    assert body["source_id"] == source_id
    assert body["indexed_chunks"] > 0


def test_index_endpoint_unknown_source_returns_404() -> None:
    notebook_id = _create_notebook()
    response = client.get(f"/notebooks/{notebook_id}/sources/nope/index")
    assert response.status_code == 404


def test_stream_emits_sse_done_event() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "text", "title": "n.txt", "content": "본문 내용입니다."},
    )
    source_id = created.json()["id"]

    with client.stream(
        "GET", f"/notebooks/{notebook_id}/sources/{source_id}/index/stream"
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("x-accel-buffering") == "no"
        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
                if events[-1]["status"] in ("done", "failed"):
                    break
    assert events
    assert events[-1]["status"] == "done"
    assert events[-1]["percent"] == 100


def test_chat_endpoint_after_indexing_returns_file_path_field() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={
            "kind": "md",
            "title": "auth.md",
            "content": "# 인증\n\nJWT 만료 시간을 확인하고 401 응답을 반환한다.",
        },
    )
    source_id = created.json()["id"]

    response = client.post(
        f"/notebooks/{notebook_id}/chat",
        json={"question": "JWT 만료 확인", "source_ids": [source_id]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    citation = body["citations"][0]
    assert citation["source_id"] == source_id
    # 기존 path 필드 유지 + file_path 별칭 추가.
    assert "path" in citation
    assert "file_path" in citation


def test_index_done_reports_last_synced_at() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "md", "title": "a.md", "content": "# t\n\n본문 내용"},
    )
    source_id = created.json()["id"]

    body = client.get(f"/notebooks/{notebook_id}/sources/{source_id}/index").json()
    assert body["status"] == "done"
    # done으로 끝났으면 last_synced_at이 채워져 있어야 한다(SSE/GET 응답 노출).
    assert body["last_synced_at"] is not None


def test_reindex_resets_progress_and_completes() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "md", "title": "a.md", "content": "# t\n\n본문 내용"},
    )
    source_id = created.json()["id"]

    # 최초 인덱싱 완료.
    first = client.get(f"/notebooks/{notebook_id}/sources/{source_id}/index").json()
    assert first["status"] == "done"

    # reindex 호출: 응답 시점에는 queued로 리셋되어 있어야 한다(register 직후 스냅샷).
    reindex = client.post(f"/notebooks/{notebook_id}/sources/{source_id}/reindex")
    assert reindex.status_code == 200
    assert reindex.json()["status"] == "queued"

    # TestClient는 BackgroundTasks를 응답 후 동기 실행하므로 재인덱싱이 끝나 있다.
    after = client.get(f"/notebooks/{notebook_id}/sources/{source_id}/index").json()
    assert after["status"] == "done"
    assert after["last_synced_at"] is not None


def test_reindex_unknown_source_returns_404() -> None:
    notebook_id = _create_notebook()
    response = client.post(f"/notebooks/{notebook_id}/sources/nope/reindex")
    assert response.status_code == 404


def test_delete_source_cleans_up_progress() -> None:
    notebook_id = _create_notebook()
    created = client.post(
        f"/notebooks/{notebook_id}/sources",
        json={"kind": "md", "title": "a.md", "content": "# t\n\n본문"},
    )
    source_id = created.json()["id"]
    assert client.get(f"/notebooks/{notebook_id}/sources/{source_id}/index").status_code == 200

    assert client.delete(f"/notebooks/{notebook_id}/sources/{source_id}").status_code == 204

    assert get_progress_registry().get(source_id) is None
