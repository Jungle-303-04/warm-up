import base64
import hashlib
import hmac
import json
import os
import time
from secrets import token_urlsafe

from app.domains.auth.domain.errors import AuthConfigurationError, AuthTokenError


JWT_ALGORITHM = "HS256"
JWT_TYPE = "JWT"
ACCESS_TOKEN_TYPE = "access"
OAUTH_STATE_TOKEN_TYPE = "github_oauth_state"
AUTH_SECRET_ENV_NAMES = ("AUTH_JWT_SECRET_KEY", "JWT_SECRET_KEY")
DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24
DEFAULT_STATE_TOKEN_EXPIRE_SECONDS = 60 * 10
JWT_PART_COUNT = 3


class JwtService:
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
        claims = self.decode(token)
        if claims.get("token_type") != ACCESS_TOKEN_TYPE:
            raise AuthTokenError("invalid auth token type")
        return claims

    def verify_github_oauth_state(self, state: str) -> None:
        claims = self.decode(state)
        if claims.get("token_type") != OAUTH_STATE_TOKEN_TYPE:
            raise AuthTokenError("invalid oauth state token type")

    def encode(self, claims: dict) -> str:
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
    for env_name in AUTH_SECRET_ENV_NAMES:
        value = os.getenv(env_name)
        if value:
            return value
    return None


def current_timestamp() -> int:
    return int(time.time())


def encode_json_part(value: dict) -> str:
    json_text = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return encode_base64_url(json_text.encode("utf-8"))


def decode_json_part(value: str) -> dict:
    try:
        decoded = decode_base64_url(value).decode("utf-8")
        result = json.loads(decoded)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthTokenError("invalid auth token payload") from exc

    if not isinstance(result, dict):
        raise AuthTokenError("invalid auth token payload")
    return result


def encode_base64_url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode_base64_url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def sign_value(value: str, secret_key: str) -> str:
    digest = hmac.new(
        secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return encode_base64_url(digest)


def split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != JWT_PART_COUNT:
        raise AuthTokenError("invalid auth token format")
    return parts[0], parts[1], parts[2]


def validate_expiration(claims: dict) -> None:
    exp = claims.get("exp")
    if not isinstance(exp, int) or exp < current_timestamp():
        raise AuthTokenError("auth token expired")


def require_secret(secret_key: str | None) -> None:
    if not secret_key:
        raise AuthConfigurationError("AUTH_JWT_SECRET_KEY is required")
