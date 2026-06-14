class GitHubFileCitationBuilder:
    """파일 단위 근거가 어느 commit의 어느 path에서 왔는지 표시한다."""

    def build(self, path: str, commit_sha: str) -> str:
        """청크 라인 정보가 없을 때 사용할 기본 citation 문자열을 만든다."""

        return f"{path}@{commit_sha}"
