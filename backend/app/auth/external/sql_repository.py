from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.external.github_schema import (
    GitHubOAuthTokenDTO,
    GitHubUserProfileDTO,
)
from app.auth.external.model import GitHubOAuthAccount
from app.user.external.model import User


class AuthSqlRepository:
    """GitHub OAuth 계정과 내부 User 행을 SQL DB에 저장하고 조회한다."""

    def get_github_account_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> GitHubOAuthAccount | None:
        """JWT subject로 저장된 OAuth 계정을 찾을 때 사용한다."""

        return db.scalar(
            select(GitHubOAuthAccount).where(GitHubOAuthAccount.user_id == user_id)
        )

    def get_github_account_by_github_user_id(
        self,
        db: Session,
        github_user_id: int,
    ) -> GitHubOAuthAccount | None:
        """동일 GitHub 계정이 다시 로그인할 때 기존 행을 갱신하기 위해 조회한다."""

        return db.scalar(
            select(GitHubOAuthAccount).where(
                GitHubOAuthAccount.github_user_id == github_user_id
            )
        )

    def upsert_github_account(
        self,
        db: Session,
        profile: GitHubUserProfileDTO,
        token: GitHubOAuthTokenDTO,
        email: str | None,
    ) -> GitHubOAuthAccount:
        """최초 로그인은 계정을 만들고, 재로그인은 토큰과 profile 정보를 최신화한다."""

        account = self.get_github_account_by_github_user_id(db, profile.id)

        if account is None:
            account = GitHubOAuthAccount(
                user_id=self.create_user(db).id,
                github_user_id=profile.id,
                login=profile.login,
                name=profile.name,
                email=email or profile.email,
                avatar_url=profile.avatar_url,
                access_token=token.access_token,
                token_type=token.token_type,
                scope=token.scope,
            )
            db.add(account)
        else:
            account.login = profile.login
            account.name = profile.name
            account.email = email or profile.email
            account.avatar_url = profile.avatar_url
            account.access_token = token.access_token
            account.token_type = token.token_type
            account.scope = token.scope

        db.commit()
        db.refresh(account)
        return account

    def create_user(self, db: Session) -> User:
        """OAuth 계정과 연결할 내부 사용자 행을 만든다."""

        user = User(id=self.next_user_id(db))
        db.add(user)
        db.flush()
        return user

    def next_user_id(self, db: Session) -> int:
        """기존 스키마의 수동 id 생성 방식을 유지하기 위해 다음 user id를 계산한다."""

        max_user_id = db.scalar(select(func.max(User.id))) or 0
        return max_user_id + 1
