"""repo-rag Postgres 엔진/세션 계층.

이 모듈은 SQLAlchemy에 의존하므로, Postgres를 사용할 때(=POSTGRES_DATABASE_URL이
설정됐을 때)만 lazy하게 import 되도록 호출부를 구성한다.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
import threading

from sqlalchemy import DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


_engine_lock = threading.Lock()
_shared_engine: Engine | None = None
_shared_session_factory: sessionmaker[Session] | None = None


def get_shared_session_factory(database_url: str) -> sessionmaker[Session]:
    """전역적으로 하나의 데이터베이스 커넥션 풀(Engine)과 세션 팩토리를 공유하여 리소스를 절약합니다."""
    global _shared_engine, _shared_session_factory
    if _shared_session_factory is None:
        with _engine_lock:
            if _shared_session_factory is None:
                _shared_engine = create_db_engine(database_url)
                _shared_session_factory = create_session_factory(_shared_engine)
    return _shared_session_factory

