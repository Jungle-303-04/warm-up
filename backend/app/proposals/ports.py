"""제안 저장소 포트 추상 정의."""

from typing import Protocol

from app.pipeline.router import ProposalStatus
from app.proposals.domain import ProposalRecord


class ProposalStore(Protocol):
    def add(self, records: list[ProposalRecord]) -> None: ...

    def list(
        self,
        *,
        repository: str | None = None,
        status: ProposalStatus | None = None,
    ) -> list[ProposalRecord]: ...

    def get(self, proposal_id: str) -> ProposalRecord: ...

    def update(self, record: ProposalRecord) -> None: ...
