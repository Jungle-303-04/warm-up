from app.pipeline.schemas import CodeReference, RetrievalChunk
from app.pipeline.agent import AgentProposalService


def test_propose_returns_empty_list_without_code_references() -> None:
    service = AgentProposalService()

    assert service.propose([], []) == []


def test_propose_creates_evidence_backed_related_code_suggestion() -> None:
    service = AgentProposalService()
    references = [
        CodeReference(
            id="app.py:login",
            path="app.py",
            symbol="login",
            line=1,
            commit_sha="abc123",
            status="verified",
        )
    ]
    chunks = [
        RetrievalChunk(
            id="app.py@abc123",
            source_path="app.py",
            text="def login(): pass",
            citation="repo:app.py@abc123",
        )
    ]

    proposals = service.propose(references, chunks)

    assert len(proposals) == 1
    assert proposals[0].status == "pending"
    assert proposals[0].evidence == ["repo:app.py@abc123"]
    assert proposals[0].confidence == 0.7
