import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.pipeline import (
    AGENT_PROPOSAL,
    APPROVAL,
    CODE_INDEX,
    DEFAULT_REPO,
    RAG_INDEX,
    REPO_SYNC,
    ProposalStatus,
)
from app.pipeline.api.router import router as pipeline_router
from app.repo_rag.api.router import router as repo_rag_router

app = FastAPI()
app.include_router(pipeline_router, prefix="/pipeline")
app.include_router(repo_rag_router, prefix="/pipeline")
client = TestClient(app)


def run_git(repo_path: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def create_git_repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "project"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True, text=True)
    run_git(repo_path, "config", "user.email", "test@example.com")
    run_git(repo_path, "config", "user.name", "Test User")
    (repo_path / "app.py").write_text("def run():\n    return True\n", encoding="utf-8")
    run_git(repo_path, "add", "app.py")
    run_git(repo_path, "commit", "-m", "initial commit")

    return repo_path


def create_bare_remote(source_repo_path: Path, tmp_path: Path) -> Path:
    remote_path = tmp_path / "remote.git"
    subprocess.run(
        ["git", "clone", "--bare", str(source_repo_path), str(remote_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return remote_path


def test_pipeline_run_route_returns_complete_response() -> None:
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
    assert body["repository"]["repository"] == DEFAULT_REPO
    assert body["code_references"]
    assert body["retrieval_chunks"]
    assert body["proposals"][0]["status"] == ProposalStatus.APPROVED
    assert [stage["id"] for stage in body["stages"]] == [
        REPO_SYNC,
        CODE_INDEX,
        RAG_INDEX,
        AGENT_PROPOSAL,
        APPROVAL,
    ]


def test_pipeline_run_route_returns_400_without_repository_source() -> None:
    response = client.post("/pipeline/run", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "repository_url 또는 files가 필요합니다"


def test_pipeline_run_route_syncs_repository_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_repo_path = create_git_repo(tmp_path)
    remote_path = create_bare_remote(source_repo_path, tmp_path)
    monkeypatch.setenv("REPOPILOT_ALLOW_FILE_REPOSITORY_URL", "1")

    response = client.post("/pipeline/run", json={"repository_url": remote_path.as_uri()})

    assert response.status_code == 200
    body = response.json()
    assert body["repository"]["repository"] == "remote"
    assert [file["path"] for file in body["repository"]["files"]] == ["app.py"]


def test_pipeline_run_route_returns_400_for_invalid_repository_url() -> None:
    response = client.post(
        "/pipeline/run",
        json={"repository_url": "https://example.com/team/project.git"},
    )

    assert response.status_code == 400
    assert "repository_url은 https://github.com/" in response.json()["detail"]


def test_pipeline_sync_route_returns_repo_rag_job_response() -> None:
    response = client.post(
        "/pipeline/sync",
        json={
            "repository": "team/api-route",
            "files": [{"path": "app.py", "content": "def run():\n    return True\n"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job"]["status"] == "succeeded"
    assert body["job"]["trigger_type"] == "manual"
    assert body["repository"]["repository"] == "team/api-route"
    assert body["changes"] == [
        {
            "path": "app.py",
            "status": "added",
            "previous_hash": None,
            "current_hash": body["changes"][0]["current_hash"],
        }
    ]
    assert body["active_chunks"][0]["source_path"] == "app.py"
    assert "diff_completed" in {event["stage"] for event in body["events"]}
