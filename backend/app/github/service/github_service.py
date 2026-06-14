from app.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO
from app.github.service.ports import GitHubFileSnapshotBuilderPort


class GitHubService:
    def __init__(
        self,
        snapshot_builder: GitHubFileSnapshotBuilderPort,
    ) -> None:
        self.snapshot_builder = snapshot_builder

    def build_file_snapshot_from_github_response(
        self,
        file_response: GitHubFileResponseDTO,
        commit_sha: str,
    ) -> GitHubFileSnapshotDTO:
        return self.snapshot_builder.build(file_response, commit_sha)
