"""GitHub App 인증.

App은 RSA 개인키로 서명한 JWT(RS256)로 자신을 증명하고, 그 JWT로 설치(installation)
액세스 토큰을 교환한다. 여기서는 JWT 생성(순수)을 담당하고, 토큰 교환은 네트워크가
필요하므로 InstallationTokenClient(포트)로 분리한다.

GitHub 제약: JWT 만료(exp)는 발급 시각 기준 최대 10분. 시계 오차를 고려해 iat을 60초
뒤로 당기고 ttl은 9분(540초) 기본값을 쓴다.
"""

import time

import jwt

MAX_TTL_SECONDS = 540
CLOCK_SKEW_SECONDS = 60


def build_app_jwt(
    app_id: str,
    private_key: str,
    *,
    now: int | None = None,
    ttl_seconds: int = MAX_TTL_SECONDS,
) -> str:
    issued_at = now if now is not None else int(time.time())
    payload = {
        "iat": issued_at - CLOCK_SKEW_SECONDS,
        "exp": issued_at + ttl_seconds,
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def load_private_key(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()
