"""ProposalStore의 Postgres 구현.

각 연산은 session_scope로 짧은 트랜잭션 경계를 잡는다(제안은 단일 애그리거트라
교차 트랜잭션이 필요 없다). add/update는 PK 기준 merge(upsert)로 처리한다.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.pipeline.api.schemas import ProposalStatus
from app.proposals.domain.ports import ProposalStore
from app.proposals.domain.records import ProposalRecord
from app.api.errors import EntityNotFoundError
from app.proposals.infrastructure.mappers import to_record, to_model
from app.proposals.infrastructure.models import ProposalModel
from app.repo_rag.infrastructure.db import session_scope


class SqlProposalStore(ProposalStore):

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, records: list[ProposalRecord]) -> None:
        with session_scope(self._session_factory) as session:
            for record in records:
                session.merge(to_model(record))

    def list(
        self,
        *,
        repository: str | None = None,
        status: ProposalStatus | None = None,
    ) -> list[ProposalRecord]:
        with session_scope(self._session_factory) as session:
            stmt = select(ProposalModel)
            if repository is not None:
                stmt = stmt.where(ProposalModel.repository == repository)
            if status is not None:
                stmt = stmt.where(ProposalModel.status == status.value)
            stmt = stmt.order_by(ProposalModel.created_at)
            return [to_record(model) for model in session.scalars(stmt).all()]

    def get(self, proposal_id: str) -> ProposalRecord:
        with session_scope(self._session_factory) as session:
            model = session.get(ProposalModel, proposal_id)
            if model is None:
                raise EntityNotFoundError(proposal_id)
            return to_record(model)

    def update(self, record: ProposalRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(to_model(record))
