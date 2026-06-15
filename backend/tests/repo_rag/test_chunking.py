from app.pipeline.api.schemas import RepoFile, RepoSnapshot
from app.repo_rag.api.schemas import RepoFileChange
from app.repo_rag.domain.chunking import ChunkingService

COMMIT = "abc123def456"


def _snapshot(files: list[RepoFile]) -> RepoSnapshot:
    return RepoSnapshot(repository="team/repo", branch="main", commit_sha=COMMIT, files=files)


def _added(*paths: str) -> list[RepoFileChange]:
    return [RepoFileChange(path=path, status="added") for path in paths]


def test_python_symbol_chunks_with_classification() -> None:
    service = ChunkingService()
    content = (
        "class UserService:\n"
        "    def login(self):\n"
        "        return True\n"
        "\n"
        "def helper():\n"
        "    return 1\n"
    )
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="app/service.py", content=content)]),
        _added("app/service.py"),
    )

    by_symbol = {chunk.symbol_name: chunk for chunk in chunks}
    assert {"UserService", "login", "helper"} <= set(by_symbol)
    assert by_symbol["UserService"].chunk_type == "python_service_class"
    assert by_symbol["login"].start_line == 2
    assert all(chunk.language == "python" for chunk in chunks)
    assert all(chunk.id.startswith(f"app/service.py@{COMMIT}:") for chunk in chunks)


def test_api_route_classification() -> None:
    service = ChunkingService()
    content = '@router.get("/items")\ndef list_items():\n    return []\n'
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="app/router.py", content=content)]),
        _added("app/router.py"),
    )
    assert chunks[0].chunk_type == "python_api_route"


def test_markdown_sections() -> None:
    service = ChunkingService()
    content = "# Title\n\nIntro\n\n## Section\n\nBody\n"
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="README.md", content=content)]),
        _added("README.md"),
    )
    assert all(chunk.chunk_type == "markdown_section" for chunk in chunks)
    assert {"Title", "Section"} <= {chunk.symbol_name for chunk in chunks}


def test_citation_includes_repository_and_line_range() -> None:
    service = ChunkingService()
    content = "def run():\n    return True\n"
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="app.py", content=content)]),
        _added("app.py"),
    )
    assert chunks[0].citation == f"team/repo:app.py:1-2@{COMMIT}"


def test_unsupported_language_is_skipped() -> None:
    service = ChunkingService()
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="data.json", content='{"a": 1}')]),
        _added("data.json"),
    )
    assert chunks == []


def test_unchanged_files_are_not_chunked() -> None:
    service = ChunkingService()
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="app.py", content="def run():\n    return True\n")]),
        [RepoFileChange(path="app.py", status="unchanged")],
    )
    assert chunks == []


def test_syntax_error_falls_back_to_plain_text() -> None:
    service = ChunkingService()
    chunks = service.chunk_changed_files(
        _snapshot([RepoFile(path="broken.py", content="def oops(:\n  pass\n")]),
        _added("broken.py"),
    )
    assert chunks
    assert all(chunk.chunk_type == "python_parse_error" for chunk in chunks)
