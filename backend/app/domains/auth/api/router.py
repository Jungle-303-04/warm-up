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
from app.domains.auth.api.dependencies import AUTH_COOKIE_NAME, resolve_auth_token
from app.domains.auth.api.schema import (
    AuthMeResponseDTO,
    AuthTokenResponseDTO,
    GitHubOAuthLoginResponseDTO,
)
from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.domain.errors import (
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
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
) -> GitHubOAuthLoginResponseDTO:
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
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
) -> RedirectResponse:
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
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
) -> AuthMeResponseDTO:
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
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookie(response)
    return response


def set_auth_cookie(response: Response, token_response: AuthTokenResponseDTO) -> None:
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
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=is_auth_cookie_secure(),
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )


def get_frontend_callback_url() -> str:
    return os.getenv(FRONTEND_CALLBACK_URL_ENV) or DEFAULT_FRONTEND_CALLBACK_URL


def is_auth_cookie_secure() -> bool:
    value = os.getenv(AUTH_COOKIE_SECURE_ENV, "")
    return value.lower() in {"1", "true", "yes", "on"}
