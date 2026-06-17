"""소스/파일 신뢰도와 코드·문서 판별 공용 헬퍼."""

from app.notebooks.domain.records import SourceRecord

CODE_EXTENSIONS = (
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".env",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
    ".cs",
    ".cpp",
    ".cc",
    ".c",
    ".h",
    ".hpp",
    ".html",
    ".css",
)

DOC_EXTENSIONS = (".md", ".markdown", ".rst", ".txt", ".adoc")
DOC_DIRECTORY_NAMES = {"doc", "docs", "documentation", "wiki"}
DOC_FILE_PREFIXES = (
    "readme",
    "changelog",
    "changes",
    "history",
    "contributing",
    "license",
    "skill",
)
DOC_LIKE_LANGUAGES = {"markdown", "text", "pdf", "url", None}


def normalize_path(path: str | None) -> str:
    return (path or "").strip().replace("\\", "/").lower()


def is_code_path(path: str | None) -> bool:
    normalized = normalize_path(path)
    if not normalized:
        return False
    filename = normalized.rsplit("/", maxsplit=1)[-1]
    return filename == "dockerfile" or any(
        normalized.endswith(ext) for ext in CODE_EXTENSIONS
    )


def is_repo_document_path(path: str | None) -> bool:
    normalized = normalize_path(path)
    if not normalized:
        return False
    parts = [part for part in normalized.split("/") if part]
    filename = parts[-1] if parts else normalized
    stem = filename.split(".", maxsplit=1)[0]
    return (
        any(part in DOC_DIRECTORY_NAMES for part in parts[:-1])
        or normalized.endswith(DOC_EXTENSIONS)
        or any(stem.startswith(prefix) for prefix in DOC_FILE_PREFIXES)
    )


def is_doc_like_language(language: str | None) -> bool:
    return (language or None) in DOC_LIKE_LANGUAGES


def is_repo_code_source(
    source: SourceRecord,
    *,
    path: str | None,
    language: str | None,
) -> bool:
    if source.kind != "repo":
        return False
    if is_repo_document_path(path):
        return False
    return is_code_path(path) or not is_doc_like_language(language)


def is_repo_document_source(
    source: SourceRecord,
    *,
    path: str | None,
    language: str | None,
) -> bool:
    if source.kind != "repo":
        return False
    return is_repo_document_path(path) or (
        bool(path) and is_doc_like_language(language) and not is_code_path(path)
    )


def trust_rank_for_source(
    source: SourceRecord,
    *,
    path: str | None = None,
    language: str | None = None,
) -> int:
    """높을수록 우선 신뢰한다."""

    if is_repo_code_source(source, path=path, language=language):
        return 50
    if is_repo_document_source(source, path=path, language=language):
        return 35
    if source.kind == "repo":
        return 40
    if source.derived_from_artifact_id:
        return 30
    if source.kind in {"md", "text", "pdf", "url"}:
        return 20
    return 10
