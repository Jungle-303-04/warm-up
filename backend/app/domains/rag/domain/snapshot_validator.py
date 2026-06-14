# RAG chunking 전에 file snapshot 필수값을 검증하는 파일
# path, commit, content 같은 값이 없는 상태로 indexing되지 않게 막음
from app.common.validation import require_value
from app.domains.github.api.schema import GitHubFileSnapshotDTO


# file snapshot validator
class SnapshotValidator:
    def validate(self, file_snapshot: GitHubFileSnapshotDTO) -> None:
        require_value(file_snapshot.path, "file_snapshot.path")
        require_value(file_snapshot.commit_sha, "file_snapshot.commit_sha")
        require_value(file_snapshot.source_type, "file_snapshot.source_type")
        require_value(file_snapshot.content_text, "file_snapshot.content_text")
        require_value(file_snapshot.language, "file_snapshot.language")


# default snapshot validator
DEFAULT_SNAPSHOT_VALIDATOR = SnapshotValidator()
