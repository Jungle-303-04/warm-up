"""GitHubCommentClient의 httpx 구현(네트워크).

설치 액세스 토큰으로 GitHub REST API에 코멘트를 작성한다.
"""

from dataclasses import dataclass

import httpx

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 10.0


@dataclass(slots=True)
class HttpGitHubCommentClient:
    token: str
    base_url: str = GITHUB_API_BASE

    def create_issue_comment(self, repository: str, issue_number: int, body: str) -> str:
        response = httpx.post(
            f"{self.base_url}/repos/{repository}/issues/{issue_number}/comments",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"body": body},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["html_url"]
