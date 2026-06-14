from app.domains.auth.domain.errors import AuthTokenError


AUTH_COOKIE_NAME = "warm_up_auth_token"


def resolve_auth_token(authorization: str | None, auth_cookie: str | None) -> str:
    if authorization:
        return extract_bearer_token(authorization)

    if auth_cookie and auth_cookie.strip():
        return auth_cookie.strip()

    raise AuthTokenError("authorization token is required")


def extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise AuthTokenError("authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthTokenError("bearer token is required")

    return token.strip()
