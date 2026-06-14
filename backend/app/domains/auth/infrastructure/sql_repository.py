from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.auth.infrastructure.github_schema import (
    GitHubOAuthTokenDTO,
    GitHubUserProfileDTO,
)
from app.domains.auth.infrastructure.model import GitHubOAuthAccount
from app.domains.user.model import User


class AuthSqlRepository:
    def get_github_account_by_user_id(
        self,
        db: Session,
        user_id: int,
    ) -> GitHubOAuthAccount | None:
        return db.scalar(
            select(GitHubOAuthAccount).where(GitHubOAuthAccount.user_id == user_id)
        )

    def get_github_account_by_github_user_id(
        self,
        db: Session,
        github_user_id: int,
    ) -> GitHubOAuthAccount | None:
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
        user = User(id=self.next_user_id(db))
        db.add(user)
        db.flush()
        return user

    def next_user_id(self, db: Session) -> int:
        max_user_id = db.scalar(select(func.max(User.id))) or 0
        return max_user_id + 1
