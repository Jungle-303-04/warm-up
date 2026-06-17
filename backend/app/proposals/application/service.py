"""제안 리뷰 유스케이스.

generate: 파이프라인을 실행해 제안을 만들고 PENDING으로 영속화한다(=퀘스트 수락).
approve/reject: 상태 전이 규칙(review.decide)을 적용하고 결정 이력을 남긴다.
저장은 ProposalStore 포트에만 의존한다(in-memory/SQL 교체 가능).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.pipeline.api.schemas import AgentProposal, PipelineRequest, ProposalStatus
from app.pipeline.application.service import PipelineService
from app.proposals.domain.ports import ProposalStore
from app.proposals.domain.records import ProposalRecord
from app.proposals.domain.review import ReviewAction, decide


from fastapi import Depends
from app.proposals.dependencies import get_proposal_store, get_pipeline_service


def get_clock() -> Callable[[], datetime]:
    return lambda: datetime.now(UTC)


@dataclass(slots=True)
class ProposalReviewService:
    store: ProposalStore = Depends(get_proposal_store)
    pipeline: PipelineService = Depends(get_pipeline_service)
    clock: Callable[[], datetime] = Depends(get_clock)

    def __post_init__(self) -> None:
        from fastapi.params import Depends as DependsClass
        if isinstance(self.clock, DependsClass):
            self.clock = self.clock.dependency()

    def generate(self, request: PipelineRequest) -> list[ProposalRecord]:
        artifacts = self.pipeline.collect(request)
        repository = artifacts.repository.repository
        now = self.clock()
        records = [
            self._to_record(repository, proposal, now)
            for proposal in artifacts.pending_proposals
        ]
        self.store.add(records)
        return records

    def list(
        self,
        *,
        repository: str | None = None,
        status: ProposalStatus | None = None,
    ) -> list[ProposalRecord]:
        return self.store.list(repository=repository, status=status)

    def get(self, proposal_id: str) -> ProposalRecord:
        return self.store.get(proposal_id)

    def approve(self, proposal_id: str, reason: str | None = None) -> ProposalRecord:
        return self._decide(proposal_id, ReviewAction.APPROVE, reason)

    def reject(self, proposal_id: str, reason: str | None = None) -> ProposalRecord:
        return self._decide(proposal_id, ReviewAction.REJECT, reason)

    def _decide(
        self,
        proposal_id: str,
        action: ReviewAction,
        reason: str | None,
    ) -> ProposalRecord:
        record = self.store.get(proposal_id)
        record.status = decide(record.status, action)
        record.decided_at = self.clock()
        record.decided_reason = reason
        self.store.update(record)
        return record

    def _to_record(
        self,
        repository: str,
        proposal: AgentProposal,
        now: datetime,
    ) -> ProposalRecord:
        return ProposalRecord(
            id=proposal.id,
            repository=repository,
            target_path=proposal.target_path,
            type=proposal.type,
            proposed_change=proposal.proposed_change,
            evidence=proposal.evidence,
            confidence=proposal.confidence,
            status=ProposalStatus.PENDING,
            created_at=now,
        )
