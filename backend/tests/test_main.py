from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import DEFAULT_REPOSITORY, PIPELINE_STAGE_IDS, ProposalStatus


client = TestClient(app)


def test_root_redirects_to_docs() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/api/docs"


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_pipeline_endpoint_returns_complete_response() -> None:
    response = client.post(
        "/pipeline/run",
        json={
            "files": [
                {
                    "path": "backend/app/api/auth.py",
                    "content": "def login(user_id: str) -> str:\n    return f'token:{user_id}'\n",
                },
                {
                    "path": "docs/auth.md",
                    "content": "# Auth\n\nLogin issues a token for the current user.\n",
                },
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == DEFAULT_REPOSITORY
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == ProposalStatus.APPROVED
    assert [stage["id"] for stage in body["stages"]] == list(PIPELINE_STAGE_IDS)
