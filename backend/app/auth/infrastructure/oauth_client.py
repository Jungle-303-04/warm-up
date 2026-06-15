"""GitHubOAuthClient의 httpx 구현(네트워크).

code를 access token으로 교환하고, 그 토큰으로 사용자 정보를 조회한다.
"""

from dataclasses import dataclass

import httpx

from app.auth.domain.records import GitHubUser

TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"
REQUEST_TIMEOUT = 10.0


@dataclass(slots=True)
class HttpGitHubOAuthClient:
    client_id: str
    client_secret: str
    redirect_uri: str

    def exchange_code(self, code: str) -> str:
        response = httpx.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError(payload.get("error_description") or "GitHub 토큰 교환에 실패했습니다")
        return token

    def fetch_user(self, access_token: str) -> GitHubUser:
        response = httpx.get(
            USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return GitHubUser(
            id=data["id"],
            login=data["login"],
            name=data.get("name"),
            avatar_url=data.get("avatar_url"),
        )
