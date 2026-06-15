"""GitHubTokenStore의 in-memory 구현(개발/테스트용)."""


class InMemoryGitHubTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[int, str] = {}

    def save(self, user_id: int, access_token: str) -> None:
        self._tokens[user_id] = access_token

    def get(self, user_id: int) -> str | None:
        return self._tokens.get(user_id)
