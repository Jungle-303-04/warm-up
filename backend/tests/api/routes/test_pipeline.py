from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.pipeline import router
from app.pipeline import PIPELINE_STAGE_IDS

app = FastAPI()
app.include_router(router, prefix="/pipeline")
client = TestClient(app)


def test_pipeline_route_returns_stage_metadata() -> None:
    response = client.get("/pipeline")

    assert response.status_code == 200
    stage_ids = [stage["id"] for stage in response.json()["stages"]]
    assert stage_ids == list(PIPELINE_STAGE_IDS)


def test_pipeline_run_route_returns_complete_response() -> None:
    response = client.post("/pipeline/run", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == "sample-repo"
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == "approved"
    assert body["publish_snapshot"]["status"] == "published"
