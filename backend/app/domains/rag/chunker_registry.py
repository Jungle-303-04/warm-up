# 언어별 chunker를 등록하고 language 값으로 찾아주는 파일
# python, markdown 등 지원 언어가 늘어나면 registry에 추가
from app.domains.rag.chunking_base import (
    DEFAULT_TEXT_SPLITTER,
    LanguageChunker,
)
from app.domains.rag.markdown_chunker import MarkdownChunker
from app.domains.rag.python_chunker import PythonChunker
from app.domains.rag.python_classifier import PythonChunkClassifier


# language -> chunker registry
class ChunkerRegistry:
    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
        return self.chunkers.get(language)


# default chunker registry
DEFAULT_CHUNKER_REGISTRY = ChunkerRegistry(
    chunkers=[
        PythonChunker(
            classifier=PythonChunkClassifier(),
            text_splitter=DEFAULT_TEXT_SPLITTER,
        ),
        MarkdownChunker(),
    ]
)
