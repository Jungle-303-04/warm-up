from sqlalchemy.orm import Session

from app.auth.api.schema import (
    AuthMeResponseDTO,
    AuthTokenResponseDTO,
    AuthenticatedUserDTO,
    GitHubOAuthLoginResponseDTO,
)
from app.auth.service.ports import (
    AuthRepositoryPort,
    AuthTokenPort,
    GitHubOAuthClientPort,
)
from app.auth.external.model import GitHubOAuthAccount


class AuthService:
    """GitHub OAuth 로그인, JWT 발급, 인증 사용자 조회 흐름을 조율한다."""

    def __init__(
        self,
        github_oauth_client: GitHubOAuthClientPort,
        jwt_service: AuthTokenPort,
        auth_repository: AuthRepositoryPort,
    ) -> None:
        self.github_oauth_client = github_oauth_client
        self.jwt_service = jwt_service
        self.auth_repository = auth_repository

    def build_github_login_response(self) -> GitHubOAuthLoginResponseDTO:
        """프론트가 GitHub 로그인 버튼 클릭 후 이동할 authorize URL과 state를 만든다."""

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
        """GitHub callback code를 교환해 계정을 저장하고 서비스용 JWT를 발급한다."""

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
        """프론트가 쿠키 기반으로 현재 로그인 사용자를 다시 확인할 때 사용한다."""

        account = self.get_authenticated_github_account(db, access_token)
        return AuthMeResponseDTO(user=self.build_authenticated_user(account))

    def get_authenticated_github_account(
        self,
        db: Session,
        access_token: str,
    ) -> GitHubOAuthAccount:
        """JWT의 user_id로 저장된 GitHub OAuth 계정을 찾아 GitHub API 호출에 재사용한다."""

        claims = self.jwt_service.verify_access_token(access_token)
        user_id = int(claims["sub"])
        account = self.auth_repository.get_github_account_by_user_id(db, user_id)

        if account is None:
            raise ValueError("authenticated github account not found")

        return account

    def build_authenticated_user(
        self,
        account: GitHubOAuthAccount,
    ) -> AuthenticatedUserDTO:
        """DB 계정 모델에서 브라우저에 노출해도 되는 사용자 정보만 응답 DTO로 옮긴다."""

        return AuthenticatedUserDTO(
            user_id=account.user_id,
            github_user_id=account.github_user_id,
            login=account.login,
            name=account.name,
            email=account.email,
            avatar_url=account.avatar_url,
        )
