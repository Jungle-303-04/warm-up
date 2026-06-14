class GitHubFileCitationBuilder:
    def build(self, path: str, commit_sha: str) -> str:
        return f"{path}@{commit_sha}"
