from app.auth.domain.errors import AuthTokenError
from app.auth.external.model import GitHubOAuthAccount
from app.auth.service.ports import AuthServicePort
from sqlalchemy.orm import Session


AUTH_COOKIE_NAME = "warm_up_auth_token"


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
