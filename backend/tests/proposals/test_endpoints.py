import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.service import PipelineService
from app.proposals.dependencies import (
    _in_memory_store as _store,
)
from app.proposals.dependencies import (
    get_pipeline_service,
)

client = TestClient(app)

_FILES = {"files": [{"path": "app.py", "content": "def login():\n    return 1\n"}]}


def _test_pipeline_service() -> PipelineService:
    return PipelineService()


@pytest.fixture(autouse=True)
def _reset_store():
    _store.cache_clear()
    app.dependency_overrides[get_pipeline_service] = _test_pipeline_service
    yield
    app.dependency_overrides.pop(get_pipeline_service, None)
    _store.cache_clear()


def _generate() -> dict:
    response = client.post("/pipeline/proposals", json=_FILES)
    assert response.status_code == 201
    return response.json()["proposals"][0]


def test_generate_creates_pending_proposal() -> None:
    proposal = _generate()

    assert proposal["status"] == "pending"
    assert proposal["target_path"] == "app.py"


def test_list_filters_by_status() -> None:
    _generate()

    pending = client.get("/pipeline/proposals", params={"status": "pending"})
    approved = client.get("/pipeline/proposals", params={"status": "approved"})

    assert len(pending.json()["proposals"]) >= 1
    assert approved.json()["proposals"] == []


def test_approve_then_reapprove_conflicts() -> None:
    proposal = _generate()
    proposal_id = proposal["id"]

    approved = client.post(f"/pipeline/proposals/{proposal_id}/approve", json={"reason": "ok"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["decided_reason"] == "ok"

    conflict = client.post(f"/pipeline/proposals/{proposal_id}/approve", json={})
    assert conflict.status_code == 409


def test_reject_transitions_to_rejected() -> None:
    proposal_id = _generate()["id"]

    rejected = client.post(f"/pipeline/proposals/{proposal_id}/reject", json={})

    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_get_unknown_proposal_returns_404() -> None:
    response = client.get("/pipeline/proposals/does-not-exist")

    assert response.status_code == 404
