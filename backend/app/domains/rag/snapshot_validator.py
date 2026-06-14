from app.common.validation import require_value
from app.domains.github.schema import GitHubFileSnapshotDTO


class SnapshotValidator:
    def validate(self, file_snapshot: GitHubFileSnapshotDTO) -> None:
        require_value(file_snapshot.path, "file_snapshot.path")
        require_value(file_snapshot.commit_sha, "file_snapshot.commit_sha")
        require_value(file_snapshot.source_type, "file_snapshot.source_type")
        require_value(file_snapshot.content_text, "file_snapshot.content_text")
        require_value(file_snapshot.language, "file_snapshot.language")


DEFAULT_SNAPSHOT_VALIDATOR = SnapshotValidator()
