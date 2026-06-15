"""ProposalRecord ↔ ProposalModel 변환(도메인 ↔ ORM 경계)."""

from app.pipeline.api.schemas import ProposalStatus, ProposalType
from app.proposals.domain.records import ProposalRecord
from app.proposals.infrastructure.models import ProposalModel


def to_model(record: ProposalRecord) -> ProposalModel:
    return ProposalModel(
        id=record.id,
        repository=record.repository,
        target_path=record.target_path,
        type=record.type.value,
        proposed_change=record.proposed_change,
        evidence=list(record.evidence),
        confidence=record.confidence,
        status=record.status.value,
        created_at=record.created_at,
        decided_at=record.decided_at,
        decided_reason=record.decided_reason,
    )


def to_record(model: ProposalModel) -> ProposalRecord:
    return ProposalRecord(
        id=model.id,
        repository=model.repository,
        target_path=model.target_path,
        type=ProposalType(model.type),
        proposed_change=model.proposed_change,
        evidence=list(model.evidence),
        confidence=model.confidence,
        status=ProposalStatus(model.status),
        created_at=model.created_at,
        decided_at=model.decided_at,
        decided_reason=model.decided_reason,
    )
