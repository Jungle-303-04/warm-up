from datetime import UTC, datetime

import pytest

from app.api.errors import DomainConflictError, EntityNotFoundError
from app.pipeline.router import PipelineRequest, ProposalStatus, RepoFile
from app.proposals.service import ProposalReviewService
from app.proposals.stores import InMemoryProposalStore

FIXED_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


def _service() -> ProposalReviewService:
    from app.pipeline.service import PipelineService
    return ProposalReviewService(
        store=InMemoryProposalStore(),
        pipeline=PipelineService(),
        clock=lambda: FIXED_NOW,
    )


def _request() -> PipelineRequest:
    return PipelineRequest(
        files=[RepoFile(path="app.py", content="def login():\n    return 1\n")],
    )


def test_generate_persists_pending_proposals() -> None:
    service = _service()

    records = service.generate(_request())

    assert len(records) == 1
    assert records[0].status == ProposalStatus.PENDING
    assert records[0].created_at == FIXED_NOW
    assert service.list(status=ProposalStatus.PENDING) == records


def test_approve_transitions_and_records_decision() -> None:
    service = _service()
    [record] = service.generate(_request())

    approved = service.approve(record.id, reason="검토 완료")

    assert approved.status == ProposalStatus.APPROVED
    assert approved.decided_at == FIXED_NOW
    assert approved.decided_reason == "검토 완료"
    assert service.list(status=ProposalStatus.PENDING) == []


def test_reject_transitions_to_rejected() -> None:
    service = _service()
    [record] = service.generate(_request())

    rejected = service.reject(record.id)

    assert rejected.status == ProposalStatus.REJECTED


def test_deciding_twice_raises() -> None:
    service = _service()
    [record] = service.generate(_request())
    service.approve(record.id)

    with pytest.raises(DomainConflictError, match="이미 처리된"):
        service.approve(record.id)


def test_get_missing_proposal_raises_key_error() -> None:
    service = _service()

    with pytest.raises(EntityNotFoundError):
        service.get("nope")
