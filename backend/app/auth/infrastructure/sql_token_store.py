"""GitHubTokenStore의 Postgres 구현.

user_id를 PK로 merge(upsert)한다. session_scope로 짧은 트랜잭션 경계를 잡는다.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from app.auth.infrastructure.models import GitHubTokenModel
from app.repo_rag.infrastructure.db import session_scope


class SqlGitHubTokenStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, user_id: int, access_token: str) -> None:
        with session_scope(self._session_factory) as session:
            session.merge(
                GitHubTokenModel(
                    user_id=user_id,
                    access_token=access_token,
                    updated_at=datetime.now(UTC),
                )
            )

    def get(self, user_id: int) -> str | None:
        with session_scope(self._session_factory) as session:
            model = session.get(GitHubTokenModel, user_id)
            return model.access_token if model is not None else None
