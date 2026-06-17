from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.pipeline.api.schemas import PipelineRequest, ProposalStatus, ProposalType
from app.proposals.domain.records import ProposalRecord


class GenerateProposalsRequest(PipelineRequest):
    """제안 생성 요청. 파이프라인 입력(repository_url 또는 files)을 그대로 재사용한다."""


class ProposalDecisionRequest(BaseModel):
    reason: str | None = None


class ProposalView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository: str
    target_path: str
    type: ProposalType
    proposed_change: str
    evidence: list[str]
    confidence: float
    status: ProposalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_reason: str | None = None

    @classmethod
    def from_record(cls, record: ProposalRecord) -> "ProposalView":
        return cls(
            id=record.id,
            repository=record.repository,
            target_path=record.target_path,
            type=record.type,
            proposed_change=record.proposed_change,
            evidence=record.evidence,
            confidence=record.confidence,
            status=record.status,
            created_at=record.created_at,
            decided_at=record.decided_at,
            decided_reason=record.decided_reason,
        )


class ProposalListResponse(BaseModel):
    proposals: list[ProposalView]
