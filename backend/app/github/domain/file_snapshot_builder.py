from app.shared.identity import hash_text
from app.shared.validation import require_value
from app.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO
from app.github.domain.content_decoder import GitHubContentDecoder
from app.github.domain.file_citation import GitHubFileCitationBuilder
from app.github.domain.language_detector import GitHubLanguageDetector


DEFAULT_SOURCE_TYPE = "github_file"


class GitHubFileSnapshotBuilder:
    """GitHub 파일 응답을 RAG 파이프라인이 신뢰할 수 있는 스냅샷 DTO로 바꾼다."""

    def __init__(
        self,
        content_decoder: GitHubContentDecoder,
        language_detector: GitHubLanguageDetector,
        citation_builder: GitHubFileCitationBuilder,
    ) -> None:
        self.content_decoder = content_decoder
        self.language_detector = language_detector
        self.citation_builder = citation_builder

    def build(
        self,
        file_response: GitHubFileResponseDTO,
        commit_sha: str,
    ) -> GitHubFileSnapshotDTO:
        """파일 본문, 언어, hash, citation을 한 번에 계산해 이후 단계의 입력을 고정한다."""

        self.validate(file_response, commit_sha)

        path = file_response.path
        content_text = self.content_decoder.decode(file_response)

        return GitHubFileSnapshotDTO(
            path=path,
            name=file_response.name,
            sha=file_response.sha,
            commit_sha=commit_sha,
            language=self.language_detector.detect(path),
            source_type=DEFAULT_SOURCE_TYPE,
            content_text=content_text,
            content_hash=hash_text(content_text),
            citation=self.citation_builder.build(path, commit_sha),
            size=file_response.size or len(content_text),
            html_url=file_response.html_url,
        )

    def validate(self, file_response: GitHubFileResponseDTO, commit_sha: str) -> None:
        """경로, 내용, commit 정보가 빠진 응답이 근거 데이터로 저장되지 않게 한다."""

        require_value(file_response.path, "file_response.path")
        require_value(file_response.content, "file_response.content")
        require_value(commit_sha, "commit_sha")
