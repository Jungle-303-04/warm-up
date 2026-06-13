from app.pipeline.schemas import PipelineRequest, RepoFile, default_files


def test_default_files_include_code_and_document_examples() -> None:
    files = default_files()

    assert [file.path for file in files] == [
        "backend/app/api/auth.py",
        "docs/auth.md",
    ]


def test_pipeline_request_uses_default_sample_repo() -> None:
    request = PipelineRequest()

    assert request.repository == "sample-repo"
    assert request.branch == "main"
    assert request.repository_path is None
    assert request.repository_url is None
    assert request.files == default_files()


def test_pipeline_request_accepts_custom_files() -> None:
    request = PipelineRequest(
        repository="team/project",
        branch="feature/login",
        files=[RepoFile(path="app.py", content="def run():\n    return True\n")],
    )

    assert request.repository == "team/project"
    assert request.branch == "feature/login"
    assert request.files[0].path == "app.py"
