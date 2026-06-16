from dataclasses import dataclass

from dependency_injector.wiring import Provide, inject
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
from app.auth.domain.errors import AuthTokenError
from app.auth.external.model import GitHubOAuthAccount
from app.auth.service.ports import AuthServicePort


AUTH_COOKIE_NAME = "warm_up_auth_token"


@dataclass(frozen=True)
class AuthRequestContext:
    """라우터가 인증 토큰의 저장 위치를 몰라도 현재 인증 사용자를 얻도록 돕는다."""

    db: Session
    auth_service: AuthServicePort
    authorization: str | None
    auth_cookie: str | None

    def has_auth_token(self) -> bool:
        return bool(self.authorization and self.authorization.strip()) or bool(
            self.auth_cookie and self.auth_cookie.strip()
        )

    def github_account(self) -> GitHubOAuthAccount:
        try:
            return resolve_github_account(
                self.db,
                self.auth_service,
                self.authorization,
                self.auth_cookie,
            )
        except AuthTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

    def user_id(self, fallback_user_id: int | None = None) -> int:
        if not self.has_auth_token() and fallback_user_id is not None:
            return fallback_user_id

        return self.github_account().user_id


@inject
def resolve_auth_context(
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_session),
    auth_service: AuthServicePort = Depends(Provide[AppContainer.auth_service]),
) -> AuthRequestContext:
    """브라우저 쿠키/Bearer 헤더/DB/인증 서비스를 하나의 요청 인증 문맥으로 묶는다."""

    return AuthRequestContext(
        db=db,
        auth_service=auth_service,
        authorization=authorization,
        auth_cookie=auth_cookie,
    )


def resolve_auth_token(authorization: str | None, auth_cookie: str | None) -> str:
    """브라우저 쿠키와 API Bearer 헤더를 같은 인증 토큰 입력으로 통일한다."""

    if authorization:
        return extract_bearer_token(authorization)

    if auth_cookie and auth_cookie.strip():
        return auth_cookie.strip()

    raise AuthTokenError("authorization token is required")


def resolve_github_account(
    db: Session,
    auth_service: AuthServicePort,
    authorization: str | None,
    auth_cookie: str | None,
) -> GitHubOAuthAccount:
    """JWT 확인 뒤 GitHub API 호출에 필요한 저장된 OAuth 계정을 꺼낸다."""

    return auth_service.get_authenticated_github_account(
        db=db,
        access_token=resolve_auth_token(authorization, auth_cookie),
    )


def extract_bearer_token(authorization: str | None) -> str:
    """Authorization 헤더가 Bearer 형식인지 확인하고 실제 토큰 부분만 분리한다."""

    if authorization is None:
        raise AuthTokenError("authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthTokenError("bearer token is required")

    return token.strip()
