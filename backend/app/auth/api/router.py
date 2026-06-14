import os

from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
from app.auth.api.dependencies import AUTH_COOKIE_NAME, resolve_auth_token
from app.auth.api.schema import (
    AuthMeResponseDTO,
    AuthTokenResponseDTO,
    GitHubOAuthLoginResponseDTO,
)
from app.auth.service.ports import AuthServicePort
from app.auth.domain.errors import (
    AuthConfigurationError,
    AuthExternalRequestError,
    AuthTokenError,
)


auth = APIRouter(prefix="/auth")

DEFAULT_FRONTEND_CALLBACK_URL = "http://localhost:5173/auth/callback"
FRONTEND_CALLBACK_URL_ENV = "GITHUB_OAUTH_FRONTEND_CALLBACK_URL"
AUTH_REDIRECT_STATUS_CODE = status.HTTP_303_SEE_OTHER
AUTH_COOKIE_SECURE_ENV = "AUTH_COOKIE_SECURE"
AUTH_COOKIE_SAMESITE = "lax"


@auth.get(
    "/github/login",
    tags=["auth"],
    response_model=GitHubOAuthLoginResponseDTO,
)
@inject
def start_github_oauth_login(
    auth_service: AuthServicePort = Depends(Provide[AppContainer.auth_service]),
) -> GitHubOAuthLoginResponseDTO:
    """프론트가 GitHub 로그인 버튼 클릭 시 사용할 authorize URL을 반환한다."""

    try:
        return auth_service.build_github_login_response()
    except AuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@auth.get(
    "/github/callback",
    tags=["auth"],
    response_model=None,
)
@inject
def handle_github_oauth_callback(
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    db: Session = Depends(get_session),
    auth_service: AuthServicePort = Depends(Provide[AppContainer.auth_service]),
) -> RedirectResponse:
    """GitHub callback을 처리해 HttpOnly 쿠키를 심고 프론트 callback 화면으로 돌려보낸다."""

    try:
        token_response = auth_service.login_with_github_callback(db, code, state)
        redirect_response = RedirectResponse(
            url=get_frontend_callback_url(),
            status_code=AUTH_REDIRECT_STATUS_CODE,
        )
        set_auth_cookie(redirect_response, token_response)
        return redirect_response
    except AuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AuthTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except AuthExternalRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@auth.get(
    "/me",
    tags=["auth"],
    response_model=AuthMeResponseDTO,
)
@inject
def read_authenticated_user(
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_session),
    auth_service: AuthServicePort = Depends(Provide[AppContainer.auth_service]),
) -> AuthMeResponseDTO:
    """브라우저가 쿠키만 가진 상태에서 현재 로그인 사용자를 확인하게 한다."""

    try:
        return auth_service.get_authenticated_user(
            db=db,
            access_token=resolve_auth_token(authorization, auth_cookie),
        )
    except (AuthConfigurationError, AuthTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@auth.post(
    "/logout",
    tags=["auth"],
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_authenticated_user() -> Response:
    """저장된 인증 쿠키를 삭제해 브라우저 세션을 종료한다."""

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookie(response)
    return response


def set_auth_cookie(response: Response, token_response: AuthTokenResponseDTO) -> None:
    """JWT를 JS에서 읽을 수 없는 HttpOnly 쿠키로 내려 세션을 유지한다."""

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token_response.access_token,
        max_age=token_response.expires_in,
        httponly=True,
        secure=is_auth_cookie_secure(),
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """로그아웃 시 브라우저가 가진 인증 쿠키를 같은 옵션으로 제거한다."""

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=is_auth_cookie_secure(),
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def get_frontend_callback_url() -> str:
    """OAuth 완료 후 돌아갈 프론트 주소를 환경별로 바꿀 수 있게 한다."""

    return os.getenv(FRONTEND_CALLBACK_URL_ENV) or DEFAULT_FRONTEND_CALLBACK_URL


def is_auth_cookie_secure() -> bool:
    """로컬 HTTP 개발과 HTTPS 배포 환경에서 쿠키 secure 옵션을 다르게 적용한다."""

    value = os.getenv(AUTH_COOKIE_SECURE_ENV, "")
    return value.lower() in {"1", "true", "yes", "on"}
