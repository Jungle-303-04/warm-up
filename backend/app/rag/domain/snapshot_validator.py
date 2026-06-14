from app.github.api.schema import GitHubFileSnapshotDTO
from app.shared.validation import require_value


class SnapshotValidator:
    """빈 파일 정보가 RAG 인덱싱으로 들어와 나중에 근거 추적을 깨뜨리지 않게 막는다."""

    def validate(self, file_snapshot: GitHubFileSnapshotDTO) -> None:
        """청크 id, citation, 검색 필터에 필요한 최소 필드를 확인한다."""

        require_value(file_snapshot.path, "file_snapshot.path")
        require_value(file_snapshot.commit_sha, "file_snapshot.commit_sha")
        require_value(file_snapshot.source_type, "file_snapshot.source_type")
        require_value(file_snapshot.content_text, "file_snapshot.content_text")
        require_value(file_snapshot.language, "file_snapshot.language")


DEFAULT_SNAPSHOT_VALIDATOR = SnapshotValidator()
