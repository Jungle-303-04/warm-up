from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.router import api_router

app = FastAPI()
app.include_router(api_router)
client = TestClient(app)


def test_api_router_redirects_root_to_docs() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/api/docs"


def test_api_router_collects_health_and_pipeline_routes() -> None:
    assert client.get("/health").status_code == 200
    assert client.post(
        "/pipeline/run",
        json={"files": [{"path": "app.py", "content": "def run(): pass\n"}]},
    ).status_code == 200


def test_pipeline_routes_document_bad_request_response() -> None:
    schema = client.get("/openapi.json").json()

    pipeline_run = schema["paths"]["/pipeline/run"]["post"]["responses"]
    repo_rag_sync = schema["paths"]["/pipeline/sync"]["post"]["responses"]

    assert pipeline_run["400"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )
    assert repo_rag_sync["400"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )
