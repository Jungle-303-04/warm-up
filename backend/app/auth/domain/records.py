"""인증 도메인 값."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitHubUser:
    id: int
    login: str
    name: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True, slots=True)
class SessionClaims:
    user_id: int
    login: str
