"""
github.service
-> GitHub에서 issue / commit / file / project 정보를 가져옴
-> 이슈 생성과 프로젝트 연결을 처리
-> RAG 또는 검증 로직이 쓰기 좋은 형태로 정리
"""
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


def build_file_snapshot_from_github_response(
    file_response: GitHubFileResponseDTO,
    commit_sha: str,
) -> GitHubFileSnapshotDTO:
    require_value(file_response.path, "file_response.path")
    require_value(file_response.content, "file_response.content")
    require_value(commit_sha, "commit_sha")

    path = file_response.path
    content_text = decode_github_file_content(file_response)
    language = detect_supported_language(path)
    content_hash = hash_text(content_text)

    return GitHubFileSnapshotDTO(
        path=path,
        name=file_response.name,
        sha=file_response.sha,
        commit_sha=commit_sha,
        language=language,
        source_type=DEFAULT_SOURCE_TYPE,
        content_text=content_text,
        content_hash=content_hash,
        citation=build_file_citation(path, commit_sha),
        size=file_response.size or len(content_text),
        html_url=file_response.html_url,
    )


def get_repository():
    return


def get_branches():
    return


# 검증용:
def get_issues():
    return


def get_commits():
    return


def get_commit_detail():
    return


def get_current_file_content():
    return


# 이슈 생성용:
def create_issue():
    return


def get_projects():
    return


def add_issue_to_project():
    return


def get_project_items():
    return


# helpers


def decode_github_file_content(file_response: GitHubFileResponseDTO) -> str:
    encoding = file_response.encoding

    if encoding in PLAIN_TEXT_ENCODINGS:
        return file_response.content

    if encoding == BASE64_ENCODING:
        return decode_base64_text(file_response.content)

    raise ValueError(f"unsupported github file encoding: {encoding}")


def detect_supported_language(path: str) -> str:
    normalized_path = path.lower()

    for extension, language in SUPPORTED_RAG_EXTENSIONS.items():
        if normalized_path.endswith(extension):
            return language

    return UNSUPPORTED_LANGUAGE


def build_file_citation(path: str, commit_sha: str) -> str:
    return f"{path}@{commit_sha}"


def decode_base64_text(content: str) -> str:
    try:
        return base64.b64decode(compact_base64_text(content)).decode(DEFAULT_TEXT_ENCODING)
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError("file_response.content must be valid utf-8 base64") from exc


def compact_base64_text(content: str) -> str:
    return "".join(content.split())
