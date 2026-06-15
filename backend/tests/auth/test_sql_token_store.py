"""GitHub 토큰 SQL 저장소 통합 테스트.

POSTGRES_DATABASE_URL이 설정된 경우에만 실행된다.
"""

import os

import pytest

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_DATABASE_URL,
    reason="POSTGRES_DATABASE_URL이 설정된 경우에만 실행합니다",
)


def _store():
    from app.auth.infrastructure.models import Base
    from app.auth.infrastructure.sql_token_store import SqlGitHubTokenStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    assert POSTGRES_DATABASE_URL is not None
    engine = create_db_engine(POSTGRES_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return SqlGitHubTokenStore(create_session_factory(engine))


def test_save_get_and_overwrite() -> None:
    store = _store()

    store.save(230139989, "gho_first")
    assert store.get(230139989) == "gho_first"

    store.save(230139989, "gho_second")
    assert store.get(230139989) == "gho_second"


def test_get_missing_returns_none() -> None:
    store = _store()

    assert store.get(999999999) is None
