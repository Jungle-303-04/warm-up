"""GitHub OAuth 인가(authorize) 단계 로직 (순수).

authorize URL 생성과 CSRF 방지용 state 발급/검증을 담당한다.
state는 로그인 시작 시 발급해 세션/쿠키에 보관하고, callback에서 상수시간 비교한다.
"""

import hmac
import secrets
from urllib.parse import urlencode

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "allow_signup": "true",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def verify_state(expected: str, received: str | None) -> bool:
    if not received:
        return False
    return hmac.compare_digest(expected, received)
