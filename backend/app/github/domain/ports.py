"""GitHub 연동 포트.

SyncTrigger: 웹훅 수신 시 저장소 동기화를 시작하는 추상.
  실제 구현은 repo_rag의 RepoRagSyncService(큐잉/인라인)를 감싼다.
"""

from typing import Protocol

from app.repo_rag.api.schemas import RepoRagSyncRequest


class SyncTrigger(Protocol):
    def trigger(self, request: RepoRagSyncRequest) -> None: ...


class GitHubCommentClient(Protocol):
    """이슈/PR에 코멘트를 작성하는 추상. 작성된 코멘트 URL을 돌려준다."""

    def create_issue_comment(self, repository: str, issue_number: int, body: str) -> str: ...
