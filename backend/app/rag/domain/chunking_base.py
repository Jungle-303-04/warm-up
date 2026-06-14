from abc import ABC, abstractmethod

from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import (
    RagChunkMetadataDTO,
    RagEvidenceChunkDraftDTO,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
TEXT_SPLIT_SEPARATORS = ["\n\n", "\n", " ", ""]
NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES = {
    "python_parse_error",
    "python_symbol_part",
}


# plain text splitter
class TextSplitter:
    """AST나 heading으로 나눠도 너무 큰 텍스트를 검색 가능한 크기로 다시 쪼갠다."""

    def split(self, text: str) -> list[str]:
        """문단, 줄, 단어 순서로 최대한 자연스러운 경계를 유지해 텍스트를 분할한다."""

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            separators=TEXT_SPLIT_SEPARATORS,
        )
        return splitter.split_text(text)


# default text splitter
DEFAULT_TEXT_SPLITTER = TextSplitter()


# language-specific chunker base class
class LanguageChunker(ABC):
    """언어별 청킹 구현이 같은 DTO 형식으로 결과를 반환하게 하는 공통 기반."""

    language: str

    @abstractmethod
    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        """파일 하나를 RAG 근거 후보 목록으로 변환한다."""

        raise NotImplementedError

    def build_chunk(
        self,
        chunk_text: str,
        chunk_type: str,
        start_line: int | None = None,
        end_line: int | None = None,
        symbol_name: str | None = None,
    ) -> RagEvidenceChunkDraftDTO:
        """언어별 청커가 공통 metadata 규칙을 직접 반복하지 않게 draft DTO를 만든다."""

        return RagEvidenceChunkDraftDTO(
            chunk_text=chunk_text,
            start_line=start_line,
            end_line=end_line,
            symbol_name=symbol_name,
            chunk_type=chunk_type,
            metadata=RagChunkMetadataDTO(
                direct_implementation_evidence=is_direct_implementation_chunk_type(chunk_type),
            ),
        )


def is_direct_implementation_chunk_type(chunk_type: str) -> bool:
    """실제 구현 근거로 봐도 되는 청크와 fallback 청크를 구분한다."""

    return (
        chunk_type.startswith("python_")
        and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )
