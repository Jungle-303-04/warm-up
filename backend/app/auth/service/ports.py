from typing import Protocol

from sqlalchemy.orm import Session

from app.auth.external.github_schema import (
    GitHubOAuthTokenDTO,
    GitHubUserProfileDTO,
)
from app.auth.external.model import GitHubOAuthAccount
from app.auth.api.schema import (
    AuthMeResponseDTO,
    AuthTokenResponseDTO,
    GitHubOAuthLoginResponseDTO,
)


class GitHubOAuthClientPort(Protocol):
    @property
    def scope_text(self) -> str: ...

    def validate_client_id(self) -> None: ...

    def build_authorize_url(self, state: str) -> str: ...

    def exchange_code(self, code: str) -> GitHubOAuthTokenDTO: ...

    def fetch_user_profile(self, access_token: str) -> GitHubUserProfileDTO: ...

    def fetch_primary_email(self, access_token: str) -> str | None: ...


class AuthTokenPort(Protocol):
    @property
    def access_token_expire_seconds(self) -> int: ...

    def create_github_oauth_state(self) -> str: ...

    def verify_github_oauth_state(self, state: str) -> None: ...

    def create_access_token(self, user_id: int, github_user_id: int) -> str: ...

    def verify_access_token(self, token: str) -> dict: ...


class AuthRepositoryPort(Protocol):
    def upsert_github_account(
        self,
        db: Session,
        profile: GitHubUserProfileDTO,
        token: GitHubOAuthTokenDTO,
        email: str | None,
    ) -> GitHubOAuthAccount: ...

    def get_github_account_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> GitHubOAuthAccount | None: ...


class AuthServicePort(Protocol):
    def build_github_login_response(self) -> GitHubOAuthLoginResponseDTO: ...

    def login_with_github_callback(
        self,
        db: Session,
        code: str,
        state: str,
    ) -> AuthTokenResponseDTO: ...

    def get_authenticated_user(
        self,
        db: Session,
        access_token: str,
    ) -> AuthMeResponseDTO: ...

    def get_authenticated_github_account(
        self,
        db: Session,
        access_token: str,
    ) -> GitHubOAuthAccount: ...
