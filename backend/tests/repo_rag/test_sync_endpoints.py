"""sync 엔드포인트 동작 (in-memory 경로).

POSTGRES_DATABASE_URL이 없으면 in-memory + 인라인 실행이므로 /sync는 200에
전체 결과를 돌려주고, /sync/{job_id}로 상태를 조회할 수 있다.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_claims
from app.auth.domain.records import SessionClaims
from app.repo_rag.api.router import router

app = FastAPI()
app.include_router(router, prefix="/pipeline")
# 보호된 라우터의 세션 인증을 더미 사용자로 우회.
app.dependency_overrides[get_current_claims] = lambda: SessionClaims(user_id=1, login="test")
client = TestClient(app)


def test_sync_runs_inline_in_memory() -> None:
    response = client.post(
        "/pipeline/sync",
        json={
            "repository": "team/inline",
            "files": [{"path": "app.py", "content": "def run():\n    return True\n"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job"]["status"] == "succeeded"
    assert body["active_chunks"][0]["source_path"] == "app.py"


def test_get_sync_job_returns_status_and_events() -> None:
    sync = client.post(
        "/pipeline/sync",
        json={
            "repository": "team/status",
            "files": [{"path": "app.py", "content": "def run():\n    return True\n"}],
        },
    ).json()
    job_id = sync["job"]["id"]

    detail = client.get(f"/pipeline/sync/{job_id}")

    assert detail.status_code == 200
    body = detail.json()
    assert body["job"]["id"] == job_id
    assert body["job"]["status"] == "succeeded"
    assert "job_succeeded" in {event["stage"] for event in body["events"]}


def test_get_sync_job_unknown_id_returns_404() -> None:
    assert client.get("/pipeline/sync/does-not-exist").status_code == 404
