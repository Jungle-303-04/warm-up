from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.container import AppContainer
from app.db.session import get_session
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
    response_model=AuthTokenResponseDTO,
)
@inject
def handle_github_oauth_callback(
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    db: Session = Depends(get_session),
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
) -> AuthTokenResponseDTO:
    try:
        return auth_service.login_with_github_callback(db, code, state)
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
    db: Session = Depends(get_session),
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service]),
) -> AuthMeResponseDTO:
    try:
        return auth_service.get_authenticated_user(
            db=db,
            access_token=extract_bearer_token(authorization),
        )
    except (AuthConfigurationError, AuthTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise AuthTokenError("authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthTokenError("bearer token is required")

    return token.strip()
