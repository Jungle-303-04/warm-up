from app.pipeline.api.schemas import ProposalStatus
from app.proposals.domain.ports import ProposalStore
from app.proposals.domain.records import ProposalRecord
from app.api.errors import EntityNotFoundError


class InMemoryProposalStore(ProposalStore):

    def __init__(self) -> None:
        self._records: dict[str, ProposalRecord] = {}

    def add(self, records: list[ProposalRecord]) -> None:
        for record in records:
            self._records[record.id] = record

    def list(
        self,
        *,
        repository: str | None = None,
        status: ProposalStatus | None = None,
    ) -> list[ProposalRecord]:
        items = list(self._records.values())
        if repository is not None:
            items = [record for record in items if record.repository == repository]
        if status is not None:
            items = [record for record in items if record.status == status]
        return sorted(items, key=lambda record: record.created_at)

    def get(self, proposal_id: str) -> ProposalRecord:
        if proposal_id not in self._records:
            raise EntityNotFoundError(proposal_id)
        return self._records[proposal_id]

    def update(self, record: ProposalRecord) -> None:
        self._records[record.id] = record
