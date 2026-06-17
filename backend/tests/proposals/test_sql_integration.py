"""제안 SQL 저장소 통합 테스트.

POSTGRES_DATABASE_URL이 설정된 경우에만 실행된다.

실행 예:
    POSTGRES_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/repolm_test \
        pytest tests/proposals/test_sql_integration.py
"""

import os
from datetime import UTC, datetime

import pytest

from app.pipeline.router import ProposalStatus, ProposalType
from app.proposals.domain import ProposalRecord

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="POSTGRES_DATABASE_URL이 설정된 경우에만 실행합니다",
)


def _store():
    from app.proposals.stores import Base, SqlProposalStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    assert POSTGRES_DATABASE_URL is not None
    engine = create_db_engine(POSTGRES_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return SqlProposalStore(create_session_factory(engine))


def _record(proposal_id: str, status: ProposalStatus = ProposalStatus.PENDING) -> ProposalRecord:
    return ProposalRecord(
        id=proposal_id,
        repository="sample-repo",
        target_path="app.py",
        type=ProposalType.RELATED_CODE,
        proposed_change="문서를 연결하세요.",
        evidence=["repo:app.py@abc123"],
        confidence=0.8,
        status=status,
        created_at=datetime.now(UTC),
    )


def test_add_get_update_and_filter() -> None:
    store = _store()
    record = _record("proposal:sql:1")

    store.add([record])
    assert store.get("proposal:sql:1").status == ProposalStatus.PENDING

    record.status = ProposalStatus.APPROVED
    store.update(record)
    assert store.get("proposal:sql:1").status == ProposalStatus.APPROVED

    approved = store.list(status=ProposalStatus.APPROVED)
    assert any(item.id == "proposal:sql:1" for item in approved)


def test_get_missing_raises_entity_not_found() -> None:
    store = _store()
    from app.api.errors import EntityNotFoundError

    with pytest.raises(EntityNotFoundError):
        store.get("proposal:sql:missing")
