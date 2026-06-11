from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import PIPELINE_STAGE_IDS


client = TestClient(app)


def test_root_redirects_to_docs() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_pipeline_endpoint_returns_stage_metadata() -> None:
    response = client.get("/pipeline")

    assert response.status_code == 200
    stage_ids = [stage["id"] for stage in response.json()["stages"]]
    assert stage_ids == list(PIPELINE_STAGE_IDS)


def test_run_pipeline_endpoint_returns_complete_response() -> None:
    response = client.post("/pipeline/run", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == "sample-repo"
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == "approved"
    assert body["publish_snapshot"]["status"] == "published"
    assert [stage["id"] for stage in body["stages"]] == list(PIPELINE_STAGE_IDS)
