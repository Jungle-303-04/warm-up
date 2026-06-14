import os
from urllib.parse import urlencode

from app.external.http import HttpClientPort, HttpRequest, HttpRequestError
from app.auth.domain.errors import (
    AuthConfigurationError,
    AuthExternalRequestError,
)
from app.auth.external.github_schema import (
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
    """GitHub OAuth 화면 이동, code 교환, 사용자 profile/email 조회를 담당한다."""

    def __init__(
        self,
        http_client: HttpClientPort,
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
        self.http_client = http_client

    def build_authorize_url(self, state: str) -> str:
        """프론트가 사용자를 GitHub 로그인 화면으로 보낼 완성된 URL을 만든다."""

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
        """GitHub callback code를 access token으로 교환한다."""

        self.validate_oauth_settings()
        payload = self.request_json(
            HttpRequest(
                method="POST",
                url=GITHUB_ACCESS_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={
                    "Accept": JSON_ACCEPT_HEADER,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            ),
            "github oauth token request failed",
        )

        if "access_token" not in payload:
            raise AuthExternalRequestError("github oauth token response is invalid")

        return GitHubOAuthTokenDTO.model_validate(payload)

    def fetch_user_profile(self, access_token: str) -> GitHubUserProfileDTO:
        """로그인한 GitHub 계정의 기본 profile 정보를 가져온다."""

        payload = self.request_json(
            HttpRequest(
                method="GET",
                url=GITHUB_USER_URL,
                headers=self.build_api_headers(access_token),
                timeout=REQUEST_TIMEOUT_SECONDS,
            ),
            "github user request failed",
        )
        return GitHubUserProfileDTO.model_validate(payload)

    def fetch_primary_email(self, access_token: str) -> str | None:
        """profile email이 비어 있을 때 사용할 검증된 기본 email을 조회한다."""

        payload = self.request_json(
            HttpRequest(
                method="GET",
                url=GITHUB_EMAILS_URL,
                headers=self.build_api_headers(access_token),
                timeout=REQUEST_TIMEOUT_SECONDS,
            ),
            "github email request failed",
        )

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
        """GitHub 사용자 API 호출에 필요한 인증/버전 헤더를 만든다."""

        return {
            "Accept": GITHUB_API_ACCEPT_HEADER,
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

    def request_json(self, request: HttpRequest, error_message: str):
        """HTTP 공통 클라이언트 오류를 OAuth 도메인에서 이해하는 예외로 바꾼다."""

        try:
            payload = self.http_client.request_json(request)
        except HttpRequestError as exc:
            raise AuthExternalRequestError(error_message) from exc

        if isinstance(payload, dict) and payload.get("error"):
            raise AuthExternalRequestError(error_message)

        return payload

    def validate_client_id(self) -> None:
        """OAuth App 설정이 없을 때 GitHub authorize URL 생성을 중단한다."""

        if not self.client_id:
            raise AuthConfigurationError("GITHUB_OAUTH_CLIENT_ID is required")

    def validate_oauth_settings(self) -> None:
        """code 교환에 필요한 client id와 secret이 모두 있는지 확인한다."""

        self.validate_client_id()
        if not self.client_secret:
            raise AuthConfigurationError("GITHUB_OAUTH_CLIENT_SECRET is required")

    @property
    def scope_text(self) -> str:
        """GitHub authorize URL에 넣을 scope 목록을 공백 구분 문자열로 만든다."""

        return " ".join(self.scopes)
