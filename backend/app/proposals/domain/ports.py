"""제안 저장소 포트.

도메인이 소유하는 추상. in-memory/SQL 어댑터가 구현한다(DIP).
get은 없는 id에 대해 KeyError를 던진다(API에서 404로 변환).
"""

from typing import Protocol

from app.pipeline.api.schemas import ProposalStatus
from app.proposals.domain.records import ProposalRecord


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
