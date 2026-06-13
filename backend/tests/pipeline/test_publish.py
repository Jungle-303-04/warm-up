from app.pipeline.schemas import AgentProposal, RepoSnapshot, RetrievalChunk
from app.pipeline.publish import PublishService


def test_publish_creates_safe_static_snapshot_path() -> None:
    service = PublishService()
    snapshot = RepoSnapshot(repository="team/project", branch="main", commit_sha="abc123", files=[])
    chunks = [
        RetrievalChunk(
            id="docs/auth.md@abc123",
            source_path="docs/auth.md",
            text="Auth docs",
            citation="team/project:docs/auth.md@abc123",
        )
    ]
    proposals = [
        AgentProposal(
            id="proposal:1",
            type="related_code_suggestion",
            status="approved",
            target_path="app.py",
            evidence=[],
            confidence=0.7,
            proposed_change="Link context",
        )
    ]

    published = service.publish(snapshot, chunks, proposals)

    assert published.id == "publish:team-project:abc123"
    assert published.status == "published"
    assert published.path == "/published/team-project"
    assert published.item_count == 1
    assert published.proposal_count == 1
