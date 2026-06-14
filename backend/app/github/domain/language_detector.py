SUPPORTED_RAG_EXTENSIONS = {
    ".py": "python",
    ".md": "markdown",
}
UNSUPPORTED_LANGUAGE = "unsupported"


class GitHubLanguageDetector:
    """파일 확장자를 MVP에서 지원하는 RAG 언어 이름으로 변환한다."""

    def detect(self, path: str) -> str:
        """Python과 Markdown만 인덱싱하고 나머지는 unsupported로 넘긴다."""

        normalized_path = path.lower()

        for extension, language in SUPPORTED_RAG_EXTENSIONS.items():
            if normalized_path.endswith(extension):
                return language

        return UNSUPPORTED_LANGUAGE
