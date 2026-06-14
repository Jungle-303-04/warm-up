SUPPORTED_RAG_EXTENSIONS = {
    ".py": "python",
    ".md": "markdown",
}
UNSUPPORTED_LANGUAGE = "unsupported"


class GitHubLanguageDetector:
    def detect(self, path: str) -> str:
        normalized_path = path.lower()

        for extension, language in SUPPORTED_RAG_EXTENSIONS.items():
            if normalized_path.endswith(extension):
                return language

        return UNSUPPORTED_LANGUAGE
