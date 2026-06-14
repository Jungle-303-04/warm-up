from typing import Protocol

from app.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO


class GitHubFileSnapshotBuilderPort(Protocol):
    def build(
        self,
        file_response: GitHubFileResponseDTO,
        commit_sha: str,
    ) -> GitHubFileSnapshotDTO: ...
