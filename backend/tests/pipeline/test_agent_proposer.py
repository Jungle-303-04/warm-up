from dataclasses import dataclass

from app.pipeline.router import CodeReference, ProposalStatus, RetrievalChunk
from app.pipeline.domain import AgentProposalService, VERIFIED
from app.pipeline.proposer import ProposalDraft


@dataclass
class _StubProposer:
    drafts: list[ProposalDraft]

    def generate(
        self,
        references: list[CodeReference],
        chunks: list[RetrievalChunk],
    ) -> list[ProposalDraft]:
        return self.drafts


def _reference() -> CodeReference:
    return CodeReference(
        id="app.py:login",
        path="app.py",
        symbol="login",
        line=1,
        commit_sha="abc123",
        status=VERIFIED,
    )


def test_propose_maps_proposer_drafts_to_pending_proposals() -> None:
    proposer = _StubProposer(
        drafts=[
            ProposalDraft(
                target_path="app.py",
                proposed_change="문서에 login 흐름을 추가하세요.",
                confidence=0.82,
                evidence=["repo:app.py@abc123"],
            )
        ]
    )
    service = AgentProposalService(proposer=proposer)

    proposals = service.propose([_reference()], [])

    assert len(proposals) == 1
    assert proposals[0].id == "proposal:app.py:0"
    assert proposals[0].status == ProposalStatus.PENDING
    assert proposals[0].evidence == ["repo:app.py@abc123"]
    assert proposals[0].confidence == 0.82


def test_propose_clamps_out_of_range_confidence() -> None:
    proposer = _StubProposer(
        drafts=[
            ProposalDraft(target_path="app.py", proposed_change="x", confidence=1.9),
        ]
    )
    service = AgentProposalService(proposer=proposer)

    proposals = service.propose([_reference()], [])

    assert proposals[0].confidence == 1.0


def test_propose_returns_empty_without_references_even_with_proposer() -> None:
    proposer = _StubProposer(drafts=[])
    service = AgentProposalService(proposer=proposer)

    assert service.propose([], []) == []
