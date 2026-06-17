"""제안 저장소 구현체 (In-Memory 및 Postgres SQL 저장소)."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.api.errors import EntityNotFoundError
from app.common.database import get_or_raise
from app.pipeline.router import ProposalStatus, ProposalType
from app.proposals.domain import ProposalRecord
from app.proposals.ports import ProposalStore
from app.repo_rag.infrastructure.db import session_scope


# --- SQL Alchemy 모델 정의 ---
class Base(DeclarativeBase):
    pass


class ProposalModel(Base):
    __tablename__ = "agent_proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository: Mapped[str] = mapped_column(String, index=True, nullable=False)
    target_path: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    proposed_change: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


# --- 모델 매퍼 정의 ---
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


# --- 인메모리 저장소 구현 ---
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


# --- SQL Postgres 저장소 구현 ---
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
            model = get_or_raise(
                session,
                ProposalModel,
                proposal_id,
                f"ProposalRecord (ID: {proposal_id})을(를) 찾을 수 없습니다.",
            )
            return to_record(model)

    def update(self, record: ProposalRecord) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(to_model(record))
