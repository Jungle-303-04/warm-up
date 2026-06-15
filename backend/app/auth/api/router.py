from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.auth.api.schemas import MeResponse
from app.auth.application.service import AuthService
from app.auth.dependencies import get_auth_service
from app.config import Settings, get_settings

router = APIRouter()

STATE_COOKIE = "rp_oauth_state"
SESSION_COOKIE = "rp_session"
STATE_TTL_SECONDS = 600


@router.get("/github/login")
def github_login(service: AuthService = Depends(get_auth_service)) -> RedirectResponse:
    url, state = service.start_login()
    response = RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        STATE_COOKIE,
        state,
        httponly=True,
        samesite="lax",
        max_age=STATE_TTL_SECONDS,
    )
    return response


@router.get("/github/callback")
def github_callback(
    code: str = Query(...),
    state: str | None = Query(default=None),
    rp_oauth_state: str | None = Cookie(default=None),
    settings: Settings = Depends(get_settings),
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    try:
        result = service.complete_login(
            code,
            received_state=state,
            expected_state=rp_oauth_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    response = RedirectResponse(
        url=settings.web_app_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        SESSION_COOKIE,
        result.session_token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    response.delete_cookie(STATE_COOKIE)
    return response


@router.get("/me", response_model=MeResponse)
def me(
    rp_session: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    if not rp_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")
    try:
        claims = service.current_user(rp_session)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 유효하지 않습니다",
        ) from exc
    return MeResponse(user_id=claims.user_id, login=claims.login)
