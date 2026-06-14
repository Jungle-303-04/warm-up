import base64
import binascii

from app.common.identity import hash_text
from app.common.validation import require_value
from app.domains.github.schema import GitHubFileResponseDTO, GitHubFileSnapshotDTO


SUPPORTED_RAG_EXTENSIONS = {
    ".py": "python",
    ".md": "markdown",
}
DEFAULT_SOURCE_TYPE = "github_file"
BASE64_ENCODING = "base64"
DEFAULT_TEXT_ENCODING = "utf-8"
PLAIN_TEXT_ENCODINGS = {DEFAULT_TEXT_ENCODING, "text"}
UNSUPPORTED_LANGUAGE = "unsupported"


class GitHubContentDecoder:
    def decode(self, file_response: GitHubFileResponseDTO) -> str:
        encoding = file_response.encoding

        if encoding in PLAIN_TEXT_ENCODINGS:
            return file_response.content

        if encoding == BASE64_ENCODING:
            return self.decode_base64_text(file_response.content)

        raise ValueError(f"unsupported github file encoding: {encoding}")

    def decode_base64_text(self, content: str) -> str:
        try:
            return base64.b64decode(self.compact_base64_text(content)).decode(
                DEFAULT_TEXT_ENCODING
            )
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValueError("file_response.content must be valid utf-8 base64") from exc

    def compact_base64_text(self, content: str) -> str:
        return "".join(content.split())


class GitHubLanguageDetector:
    def detect(self, path: str) -> str:
        normalized_path = path.lower()

        for extension, language in SUPPORTED_RAG_EXTENSIONS.items():
            if normalized_path.endswith(extension):
                return language

        return UNSUPPORTED_LANGUAGE


class GitHubFileCitationBuilder:
    def build(self, path: str, commit_sha: str) -> str:
        return f"{path}@{commit_sha}"


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


def decode_github_file_content(file_response: GitHubFileResponseDTO) -> str:
    return GitHubContentDecoder().decode(file_response)


def detect_supported_language(path: str) -> str:
    return GitHubLanguageDetector().detect(path)


def build_file_citation(path: str, commit_sha: str) -> str:
    return GitHubFileCitationBuilder().build(path, commit_sha)


def decode_base64_text(content: str) -> str:
    return GitHubContentDecoder().decode_base64_text(content)


def compact_base64_text(content: str) -> str:
    return GitHubContentDecoder().compact_base64_text(content)
