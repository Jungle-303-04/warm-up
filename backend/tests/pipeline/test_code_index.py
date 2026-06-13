from app.pipeline.api.schemas import RepoFile, RepoSnapshot
from app.pipeline.domain.constants import CODE_REFERENCE_STATUS_VERIFIED
from app.pipeline.domain.code_index import CodeIndexService


def test_index_extracts_python_function_symbols() -> None:
    service = CodeIndexService()
    snapshot = RepoSnapshot(
        repository="sample",
        branch="main",
        commit_sha="abc123",
        files=[
            RepoFile(
                path="app.py",
                content="async def fetch():\n    pass\n\ndef login():\n    pass\n",
            )
        ],
    )

    references = service.index(snapshot)

    assert [(reference.symbol, reference.line) for reference in references] == [
        ("fetch", 1),
        ("login", 4),
    ]


def test_index_falls_back_to_file_reference_when_no_symbol_exists() -> None:
    service = CodeIndexService()
    snapshot = RepoSnapshot(
        repository="sample",
        branch="main",
        commit_sha="abc123",
        files=[RepoFile(path="README.md", content="# Readme\n")],
    )

    references = service.index(snapshot)

    assert len(references) == 1
    assert references[0].id == "README.md:file"
    assert references[0].symbol == "file"
    assert references[0].status == CODE_REFERENCE_STATUS_VERIFIED
