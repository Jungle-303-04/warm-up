import os
from urllib.parse import urlencode

import httpx

from app.domains.auth.domain.errors import (
    AuthConfigurationError,
    AuthExternalRequestError,
)
from app.domains.auth.infrastructure.github_schema import (
    GitHubEmailDTO,
    GitHubOAuthTokenDTO,
    GitHubUserProfileDTO,
)


GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
DEFAULT_REDIRECT_URI = "http://localhost:8000/auth/github/callback"
DEFAULT_SCOPES = ("read:user", "user:email", "repo")
REQUEST_TIMEOUT_SECONDS = 10
JSON_ACCEPT_HEADER = "application/json"
GITHUB_API_ACCEPT_HEADER = "application/vnd.github+json"
GITHUB_API_VERSION = "2022-11-28"
USER_AGENT = "warm-up-code-trust-kanban"


class GitHubOAuthClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        scopes: tuple[str, ...] = DEFAULT_SCOPES,
    ) -> None:
        self.client_id = client_id or os.getenv("GITHUB_OAUTH_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
        self.redirect_uri = (
            redirect_uri
            or os.getenv("GITHUB_OAUTH_REDIRECT_URI")
            or DEFAULT_REDIRECT_URI
        )
        self.scopes = scopes

    def build_authorize_url(self, state: str) -> str:
        self.validate_client_id()
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": self.scope_text,
                "state": state,
                "allow_signup": "true",
            }
        )
        return f"{GITHUB_AUTHORIZE_URL}?{query}"

    def exchange_code(self, code: str) -> GitHubOAuthTokenDTO:
        self.validate_oauth_settings()
        response = httpx.post(
            GITHUB_ACCESS_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            headers={
                "Accept": JSON_ACCEPT_HEADER,
                "User-Agent": USER_AGENT,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        payload = parse_json_response(response, "github oauth token request failed")

        if "access_token" not in payload:
            raise AuthExternalRequestError("github oauth token response is invalid")

        return GitHubOAuthTokenDTO.model_validate(payload)

    def fetch_user_profile(self, access_token: str) -> GitHubUserProfileDTO:
        response = httpx.get(
            GITHUB_USER_URL,
            headers=self.build_api_headers(access_token),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        payload = parse_json_response(response, "github user request failed")
        return GitHubUserProfileDTO.model_validate(payload)

    def fetch_primary_email(self, access_token: str) -> str | None:
        response = httpx.get(
            GITHUB_EMAILS_URL,
            headers=self.build_api_headers(access_token),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        payload = parse_json_response(response, "github email request failed")

        if not isinstance(payload, list):
            raise AuthExternalRequestError("github email response is invalid")

        emails = [GitHubEmailDTO.model_validate(item) for item in payload]
        primary_verified = [
            email.email for email in emails if email.primary and email.verified
        ]
        if primary_verified:
            return primary_verified[0]

        verified = [email.email for email in emails if email.verified]
        return verified[0] if verified else None

    def build_api_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Accept": GITHUB_API_ACCEPT_HEADER,
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    def validate_client_id(self) -> None:
        if not self.client_id:
            raise AuthConfigurationError("GITHUB_OAUTH_CLIENT_ID is required")

    def validate_oauth_settings(self) -> None:
        self.validate_client_id()
        if not self.client_secret:
            raise AuthConfigurationError("GITHUB_OAUTH_CLIENT_SECRET is required")

    @property
    def scope_text(self) -> str:
        return " ".join(self.scopes)


def parse_json_response(response: httpx.Response, error_message: str):
    try:
        payload = response.json()
    except ValueError as exc:
        raise AuthExternalRequestError(error_message) from exc

    if response.status_code >= 400:
        raise AuthExternalRequestError(error_message)

    if isinstance(payload, dict) and payload.get("error"):
        raise AuthExternalRequestError(error_message)

    return payload
