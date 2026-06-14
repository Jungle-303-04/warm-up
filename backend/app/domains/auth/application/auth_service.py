from sqlalchemy.orm import Session

from app.domains.auth.api.schema import (
    AuthMeResponseDTO,
    AuthTokenResponseDTO,
    AuthenticatedUserDTO,
    GitHubOAuthLoginResponseDTO,
)
from app.domains.auth.domain.jwt_service import JwtService
from app.domains.auth.infrastructure.github_oauth_client import GitHubOAuthClient
from app.domains.auth.infrastructure.model import GitHubOAuthAccount
from app.domains.auth.infrastructure.sql_repository import AuthSqlRepository


class AuthService:
    def __init__(
        self,
        github_oauth_client: GitHubOAuthClient,
        jwt_service: JwtService,
        auth_repository: AuthSqlRepository,
    ) -> None:
        self.github_oauth_client = github_oauth_client
        self.jwt_service = jwt_service
        self.auth_repository = auth_repository

    def build_github_login_response(self) -> GitHubOAuthLoginResponseDTO:
        self.github_oauth_client.validate_client_id()
        state = self.jwt_service.create_github_oauth_state()
        return GitHubOAuthLoginResponseDTO(
            authorize_url=self.github_oauth_client.build_authorize_url(state),
            state=state,
            scope=self.github_oauth_client.scope_text,
        )

    def login_with_github_callback(
        self,
        db: Session,
        code: str,
        state: str,
    ) -> AuthTokenResponseDTO:
        self.jwt_service.verify_github_oauth_state(state)

        github_token = self.github_oauth_client.exchange_code(code)
        github_profile = self.github_oauth_client.fetch_user_profile(
            github_token.access_token
        )
        github_email = self.github_oauth_client.fetch_primary_email(
            github_token.access_token
        )
        account = self.auth_repository.upsert_github_account(
            db=db,
            profile=github_profile,
            token=github_token,
            email=github_email,
        )

        access_token = self.jwt_service.create_access_token(
            user_id=account.user_id,
            github_user_id=account.github_user_id,
        )
        return AuthTokenResponseDTO(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.jwt_service.access_token_expire_seconds,
            user=self.build_authenticated_user(account),
        )

    def get_authenticated_user(self, db: Session, access_token: str) -> AuthMeResponseDTO:
        claims = self.jwt_service.verify_access_token(access_token)
        user_id = int(claims["sub"])
        account = self.auth_repository.get_github_account_by_user_id(db, user_id)

        if account is None:
            raise ValueError("authenticated github account not found")

        return AuthMeResponseDTO(user=self.build_authenticated_user(account))

    def build_authenticated_user(
        self,
        account: GitHubOAuthAccount,
    ) -> AuthenticatedUserDTO:
        return AuthenticatedUserDTO(
            user_id=account.user_id,
            github_user_id=account.github_user_id,
            login=account.login,
            name=account.name,
            email=account.email,
            avatar_url=account.avatar_url,
        )
