"""인증 의존성 배선.

GitHub access token 저장소는 프로세스 단일 인스턴스(lru_cache)로 유지한다.
OAuth client_id/secret이 없으면 503으로 안내한다(로그인 자체가 불가).
"""

from functools import lru_cache

from fastapi import Cookie, Depends, HTTPException, status

from app.auth.application.service import AuthService
from app.auth.domain.ports import GitHubTokenStore
from app.auth.domain.records import SessionClaims
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.auth.infrastructure.session_tokens import SessionTokenCodec
from app.config import Settings, get_settings


@lru_cache(maxsize=1)
def _in_memory_token_store() -> InMemoryGitHubTokenStore:
    return InMemoryGitHubTokenStore()


@lru_cache(maxsize=1)
def _sql_token_store() -> GitHubTokenStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.auth.infrastructure.sql_token_store import SqlGitHubTokenStore
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))
    return SqlGitHubTokenStore(session_factory)


def _resolve_token_store(settings: Settings) -> GitHubTokenStore:
    return _sql_token_store() if settings.uses_postgres else _in_memory_token_store()


def get_github_token_store(settings: Settings = Depends(get_settings)) -> GitHubTokenStore:
    return _resolve_token_store(settings)


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    if not settings.github_oauth_client_id or not settings.github_oauth_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth가 설정되지 않았습니다",
        )

    from app.auth.infrastructure.oauth_client import HttpGitHubOAuthClient

    oauth_client = HttpGitHubOAuthClient(
        client_id=settings.github_oauth_client_id,
        client_secret=settings.github_oauth_client_secret,
        redirect_uri=settings.github_oauth_redirect_uri,
    )
    codec = SessionTokenCodec(
        secret=settings.session_jwt_secret,
        ttl_seconds=settings.session_ttl_seconds,
    )
    return AuthService(
        oauth_client=oauth_client,
        token_store=_resolve_token_store(settings),
        session_codec=codec,
        client_id=settings.github_oauth_client_id,
        redirect_uri=settings.github_oauth_redirect_uri,
        scope=settings.github_oauth_scopes,
    )


def get_current_claims(
    rp_session: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
) -> SessionClaims:
    if not rp_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")
    try:
        return service.current_user(rp_session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 유효하지 않습니다",
        ) from exc
