import pytest
from pydantic import ValidationError

from app.pipeline.api.schemas import PipelineRequest, RepoFile


def test_pipeline_request_uses_default_sample_repo() -> None:
    request = PipelineRequest()

    assert request.repository == "sample-repo"
    assert request.branch == "main"
    assert request.repository_url is None
    assert request.files == []


def test_pipeline_request_accepts_custom_files() -> None:
    request = PipelineRequest(
        repository="team/project",
        branch="feature/login",
        files=[RepoFile(path="app.py", content="def run():\n    return True\n")],
    )

    assert request.repository == "team/project"
    assert request.branch == "feature/login"
    assert request.files[0].path == "app.py"


@pytest.mark.parametrize("path", ["", "/app.py", "../app.py", "docs/../app.py"])
def test_repo_file_rejects_invalid_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        RepoFile(path=path, content="text\n")


def test_pipeline_request_rejects_empty_repository_url() -> None:
    with pytest.raises(ValidationError):
        PipelineRequest(repository_url=" ")
