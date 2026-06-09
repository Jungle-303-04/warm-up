from app.schemas.pipeline import CodeReference, RepoFile, RepoSnapshot
from app.services.rag_index import RagIndexService


def test_index_creates_chunks_only_for_referenced_nonempty_files() -> None:
    service = RagIndexService()
    snapshot = RepoSnapshot(
        repository="sample",
        branch="main",
        commit_sha="abc123",
        files=[
            RepoFile(path="app.py", content="def login(): pass\n"),
            RepoFile(path="ignored.py", content="def ignored(): pass\n"),
            RepoFile(path="empty.py", content="   "),
        ],
    )
    references = [
        CodeReference(
            id="app.py:login",
            path="app.py",
            symbol="login",
            line=1,
            commit_sha="abc123",
            status="verified",
        ),
        CodeReference(
            id="empty.py:file",
            path="empty.py",
            symbol="file",
            line=1,
            commit_sha="abc123",
            status="verified",
        ),
    ]

    chunks = service.index(snapshot, references)

    assert len(chunks) == 1
    assert chunks[0].id == "app.py@abc123"
    assert chunks[0].citation == "sample:app.py@abc123"
