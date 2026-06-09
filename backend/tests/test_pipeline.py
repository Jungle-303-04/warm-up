from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_pipeline_has_minimum_stages() -> None:
    response = client.get("/pipeline")

    assert response.status_code == 200
    stage_ids = {stage["id"] for stage in response.json()["stages"]}
    assert {
        "repo-sync",
        "code-index",
        "rag-index",
        "agent-proposal",
        "approval",
        "static-publish",
    }.issubset(stage_ids)


def test_pipeline_run_returns_approved_publish_snapshot() -> None:
    response = client.post("/pipeline/run", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == "sample-repo"
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == "approved"
    assert body["publish_snapshot"]["status"] == "published"
    assert [stage["id"] for stage in body["stages"]] == [
        "repo-sync",
        "code-index",
        "rag-index",
        "agent-proposal",
        "approval",
        "static-publish",
    ]
