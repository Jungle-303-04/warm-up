from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import PIPELINE_STAGE_IDS


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_pipeline_has_minimum_stages() -> None:
    response = client.get("/pipeline")

    assert response.status_code == 200
    stage_ids = [stage["id"] for stage in response.json()["stages"]]
    assert stage_ids == list(PIPELINE_STAGE_IDS)
    assert len(stage_ids) == len(set(stage_ids))


def test_pipeline_run_returns_approved_publish_snapshot() -> None:
    response = client.post("/pipeline/run", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == "sample-repo"
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == "approved"
    assert body["publish_snapshot"]["status"] == "published"
    assert [stage["id"] for stage in body["stages"]] == list(PIPELINE_STAGE_IDS)
