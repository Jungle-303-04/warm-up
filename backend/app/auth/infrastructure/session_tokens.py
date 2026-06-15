"""세션 JWT(HS256) 발급/검증.

OAuth 로그인 성공 후 발급하는 우리 서비스 자체 세션 토큰이다.
GitHub access token이 아니라, 사용자 식별과 로그인 유지를 위한 짧은 수명의 토큰이다.
"""

import time
from dataclasses import dataclass

import jwt

from app.auth.domain.records import SessionClaims

ALGORITHM = "HS256"


@dataclass(slots=True)
class SessionTokenCodec:
    secret: str
    ttl_seconds: int

    def issue(self, user_id: int, login: str, *, now: int | None = None) -> str:
        issued_at = now if now is not None else int(time.time())
        payload = {
            "sub": str(user_id),
            "login": login,
            "iat": issued_at,
            "exp": issued_at + self.ttl_seconds,
        }
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)

    def verify(self, token: str) -> SessionClaims:
        try:
            claims = jwt.decode(token, self.secret, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError as exc:
            raise ValueError("유효하지 않은 세션 토큰입니다") from exc
        return SessionClaims(user_id=int(claims["sub"]), login=claims["login"])
