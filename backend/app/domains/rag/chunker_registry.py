from app.domains.rag.chunking_base import (
    DEFAULT_TEXT_SPLITTER,
    LanguageChunker,
)
from app.domains.rag.markdown_chunker import MarkdownChunker
from app.domains.rag.python_chunker import PythonChunker
from app.domains.rag.python_classifier import PythonChunkClassifier


class ChunkerRegistry:
    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
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
