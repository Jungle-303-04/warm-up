"""Postgres용 Unit of Work.

with 블록 진입 시 세션을 열고 저장소를 바인딩, 정상 종료 시 commit / 예외 시
rollback 한다. 한 블록 안의 모든 저장소 호출이 하나의 트랜잭션을 공유한다.
"""

from sqlalchemy.orm import Session, sessionmaker

from app.repo_rag.infrastructure.sql_store import SqlRepoRagStore


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._repo_rag: SqlRepoRagStore | None = None

    @property
    def session(self) -> Session:
        """컨텍스트 매니저 진입 후에만 사용 가능한 세션."""
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used within a context manager")
        return self._session

    @property
    def repo_rag(self) -> SqlRepoRagStore:
        """컨텍스트 매니저 진입 후에만 사용 가능한 저장소."""
        if self._repo_rag is None:
            raise RuntimeError("UnitOfWork must be used within a context manager")
        return self._repo_rag

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = self._session_factory()
        self._repo_rag = SqlRepoRagStore(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                if self._session:
                    self._session.rollback()
            else:
                if self._session:
                    self._session.commit()
        finally:
            if self._session:
                self._session.close()
        return None
