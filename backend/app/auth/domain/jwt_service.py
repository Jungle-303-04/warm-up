import base64
import hashlib
import hmac
import json
import os
import time
from secrets import token_urlsafe

from app.auth.domain.errors import AuthConfigurationError, AuthTokenError


JWT_ALGORITHM = "HS256"
JWT_TYPE = "JWT"
ACCESS_TOKEN_TYPE = "access"
OAUTH_STATE_TOKEN_TYPE = "github_oauth_state"
AUTH_SECRET_ENV_NAMES = ("AUTH_JWT_SECRET_KEY", "JWT_SECRET_KEY")
DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24
DEFAULT_STATE_TOKEN_EXPIRE_SECONDS = 60 * 10
JWT_PART_COUNT = 3


class JwtService:
    """외부 라이브러리 없이 OAuth state와 서비스 access token을 같은 규칙으로 서명한다."""

    def __init__(
        self,
        secret_key: str | None = None,
        access_token_expire_seconds: int = DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS,
        state_token_expire_seconds: int = DEFAULT_STATE_TOKEN_EXPIRE_SECONDS,
    ) -> None:
        self.secret_key = secret_key or load_auth_secret()
        self.access_token_expire_seconds = access_token_expire_seconds
        self.state_token_expire_seconds = state_token_expire_seconds

    def create_access_token(self, user_id: int, github_user_id: int) -> str:
        """로그인 완료 후 API 세션 유지에 사용할 짧은 claim 집합의 JWT를 만든다."""

        now = current_timestamp()
        return self.encode(
            {
                "sub": str(user_id),
                "github_user_id": github_user_id,
                "token_type": ACCESS_TOKEN_TYPE,
                "iat": now,
                "exp": now + self.access_token_expire_seconds,
            }
        )

    def create_github_oauth_state(self) -> str:
        """GitHub callback 위조를 막기 위해 만료 시간이 있는 state 토큰을 만든다."""

        now = current_timestamp()
        return self.encode(
            {
                "nonce": token_urlsafe(24),
                "token_type": OAUTH_STATE_TOKEN_TYPE,
                "iat": now,
                "exp": now + self.state_token_expire_seconds,
            }
        )

    def verify_access_token(self, token: str) -> dict:
        """API 요청에 쓰인 토큰이 access token 용도인지 확인하고 claim을 반환한다."""

        claims = self.decode(token)
        if claims.get("token_type") != ACCESS_TOKEN_TYPE:
            raise AuthTokenError("invalid auth token type")
        return claims

    def verify_github_oauth_state(self, state: str) -> None:
        """callback으로 돌아온 state가 로그인 시작 시 만든 OAuth state인지 확인한다."""

        claims = self.decode(state)
        if claims.get("token_type") != OAUTH_STATE_TOKEN_TYPE:
            raise AuthTokenError("invalid oauth state token type")

    def encode(self, claims: dict) -> str:
        """header와 claims를 base64url로 묶고 HMAC 서명을 붙여 JWT 문자열을 만든다."""

        require_secret(self.secret_key)
        header = {"alg": JWT_ALGORITHM, "typ": JWT_TYPE}
        signing_input = ".".join(
            [
                encode_json_part(header),
                encode_json_part(claims),
            ]
        )
        signature = sign_value(signing_input, self.secret_key)
        return f"{signing_input}.{signature}"

    def decode(self, token: str) -> dict:
        """JWT 서명, 알고리즘, 만료 시간을 검증한 뒤 claims를 반환한다."""

        require_secret(self.secret_key)
        header_part, payload_part, signature_part = split_token(token)
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = sign_value(signing_input, self.secret_key)

        if not hmac.compare_digest(signature_part, expected_signature):
            raise AuthTokenError("invalid auth token signature")

        header = decode_json_part(header_part)
        if header.get("alg") != JWT_ALGORITHM:
            raise AuthTokenError("unsupported auth token algorithm")

        claims = decode_json_part(payload_part)
        validate_expiration(claims)
        return claims


def load_auth_secret() -> str | None:
    """개발 환경 변수 이름 변경을 허용하기 위해 후보 env에서 secret을 찾는다."""

    for env_name in AUTH_SECRET_ENV_NAMES:
        value = os.getenv(env_name)
        if value:
            return value
    return None


def current_timestamp() -> int:
    """토큰 발급/만료 비교에 쓸 현재 Unix timestamp를 만든다."""

    return int(time.time())


def encode_json_part(value: dict) -> str:
    """JWT header/payload JSON을 서명 가능한 base64url 문자열로 바꾼다."""

    json_text = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return encode_base64_url(json_text.encode("utf-8"))


def decode_json_part(value: str) -> dict:
    """JWT header/payload 문자열을 dict로 복원하고 형식을 검증한다."""

    try:
        decoded = decode_base64_url(value).decode("utf-8")
        result = json.loads(decoded)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthTokenError("invalid auth token payload") from exc

    if not isinstance(result, dict):
        raise AuthTokenError("invalid auth token payload")
    return result


def encode_base64_url(value: bytes) -> str:
    """JWT 표준에 맞게 padding 없는 URL-safe base64 문자열을 만든다."""

    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode_base64_url(value: str) -> bytes:
    """padding이 생략된 JWT base64url 값을 다시 bytes로 복원한다."""

    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def sign_value(value: str, secret_key: str) -> str:
    """토큰 변조 여부를 확인할 수 있도록 HMAC-SHA256 서명을 만든다."""

    digest = hmac.new(
        secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return encode_base64_url(digest)


def split_token(token: str) -> tuple[str, str, str]:
    """JWT가 header.payload.signature 세 부분인지 확인하고 분리한다."""

    parts = token.split(".")
    if len(parts) != JWT_PART_COUNT:
        raise AuthTokenError("invalid auth token format")
    return parts[0], parts[1], parts[2]


def validate_expiration(claims: dict) -> None:
    """만료 시간이 없거나 지난 토큰이 API 접근에 쓰이지 않게 한다."""

    exp = claims.get("exp")
    if not isinstance(exp, int) or exp < current_timestamp():
        raise AuthTokenError("auth token expired")


def require_secret(secret_key: str | None) -> None:
    """서명 secret 없이 서버가 토큰을 발급하거나 검증하지 못하게 막는다."""

    if not secret_key:
        raise AuthConfigurationError("AUTH_JWT_SECRET_KEY is required")
