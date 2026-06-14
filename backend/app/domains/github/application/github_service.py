from app.domains.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO
from app.domains.github.domain.file_snapshot_builder import GitHubFileSnapshotBuilder


class GitHubService:
    def __init__(
        self,
        snapshot_builder: GitHubFileSnapshotBuilder,
    ) -> None:
        self.snapshot_builder = snapshot_builder

    def build_file_snapshot_from_github_response(
        self,
        file_response: GitHubFileResponseDTO,
        commit_sha: str,
    ) -> GitHubFileSnapshotDTO:
        return self.snapshot_builder.build(file_response, commit_sha)

    def get_repository(self):
        return

    def get_branches(self):
        return

    def get_issues(self):
        return

    def get_commits(self):
        return

    def get_commit_detail(self):
        return

    def get_current_file_content(self):
        return

    def create_issue(self):
        return

    def get_projects(self):
        return

    def add_issue_to_project(self):
        return

    def get_project_items(self):
        return
