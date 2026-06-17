from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.pipeline.router import AgentProposal, PipelineRequest, ProposalStatus
from app.pipeline.service import PipelineService
from app.proposals.domain import ProposalRecord, ReviewAction, decide
from app.proposals.ports import ProposalStore


def get_clock() -> Any:
    return lambda: datetime.now(UTC)


@dataclass(slots=True)
class ProposalReviewService:
    store: ProposalStore
    pipeline: PipelineService = field(default_factory=PipelineService)
    clock: Any = field(default_factory=get_clock)

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
