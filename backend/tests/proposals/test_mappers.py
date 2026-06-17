from datetime import UTC, datetime

from app.pipeline.api.schemas import ProposalStatus, ProposalType
from app.proposals.domain import ProposalRecord
from app.proposals.stores import to_model, to_record


def test_record_model_roundtrip_preserves_fields() -> None:
    record = ProposalRecord(
        id="proposal:app.py:0",
        repository="sample-repo",
        target_path="app.py",
        type=ProposalType.RELATED_CODE,
        proposed_change="문서를 연결하세요.",
        evidence=["repo:app.py@abc123"],
        confidence=0.8,
        status=ProposalStatus.APPROVED,
        created_at=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        decided_at=datetime(2026, 6, 15, 12, 5, tzinfo=UTC),
        decided_reason="검토 완료",
    )

    restored = to_record(to_model(record))

    assert restored == record
