from app.rag.domain.chunking_base import DEFAULT_TEXT_SPLITTER, LanguageChunker
from app.rag.domain.markdown_chunker import MarkdownChunker
from app.rag.domain.python_chunker import PythonChunker
from app.rag.domain.python_classifier import PythonChunkClassifier


class ChunkerRegistry:
    """파일 언어에 맞는 chunker를 찾아 새 언어 추가 시 분기문 증가를 막는다."""

    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
        """지원하지 않는 언어는 None으로 돌려 MVP 범위 밖 파일을 건너뛰게 한다."""

        return self.chunkers.get(language)


DEFAULT_CHUNKER_REGISTRY = ChunkerRegistry(
    chunkers=[
        PythonChunker(
            classifier=PythonChunkClassifier(),
            text_splitter=DEFAULT_TEXT_SPLITTER,
        ),
        MarkdownChunker(),
    ]
)
