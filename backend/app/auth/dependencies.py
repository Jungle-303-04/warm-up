"""인증 의존성 배선.

GitHub access token 저장소는 프로세스 단일 인스턴스(lru_cache)로 유지한다.
OAuth client_id/secret이 없으면 503으로 안내한다(로그인 자체가 불가).
"""

from functools import lru_cache

from fastapi import Depends, HTTPException, status

from app.auth.application.service import AuthService
from app.auth.infrastructure.in_memory_token_store import InMemoryGitHubTokenStore
from app.auth.infrastructure.session_tokens import SessionTokenCodec
from app.config import Settings, get_settings


@lru_cache(maxsize=1)
def _token_store() -> InMemoryGitHubTokenStore:
    return InMemoryGitHubTokenStore()


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
        token_store=_token_store(),
        session_codec=codec,
        client_id=settings.github_oauth_client_id,
        redirect_uri=settings.github_oauth_redirect_uri,
        scope=settings.github_oauth_scopes,
    )
