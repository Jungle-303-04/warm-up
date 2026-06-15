"""인증 포트.

GitHubOAuthClient: code→access token 교환과 사용자 조회(네트워크 어댑터가 구현).
GitHubTokenStore: 사용자별 GitHub access token 보관(이후 repo clone·코멘트에 사용).
"""

from typing import Protocol

from app.auth.domain.records import GitHubUser


class GitHubOAuthClient(Protocol):
    def exchange_code(self, code: str) -> str: ...

    def fetch_user(self, access_token: str) -> GitHubUser: ...


class GitHubTokenStore(Protocol):
    def save(self, user_id: int, access_token: str) -> None: ...

    def get(self, user_id: int) -> str | None: ...
