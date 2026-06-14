from app.common.identity import hash_text
from app.common.validation import require_value
from app.domains.github.api.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO
from app.domains.github.domain.content_decoder import GitHubContentDecoder
from app.domains.github.domain.file_citation import GitHubFileCitationBuilder
from app.domains.github.domain.language_detector import GitHubLanguageDetector


DEFAULT_SOURCE_TYPE = "github_file"


class GitHubFileSnapshotBuilder:
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
        require_value(file_response.path, "file_response.path")
        require_value(file_response.content, "file_response.content")
        require_value(commit_sha, "commit_sha")
