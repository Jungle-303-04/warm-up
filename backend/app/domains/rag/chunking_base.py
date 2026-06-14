from abc import ABC, abstractmethod

from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import (
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


class TextSplitter:
    def split(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            separators=TEXT_SPLIT_SEPARATORS,
        )
        return splitter.split_text(text)


DEFAULT_TEXT_SPLITTER = TextSplitter()


class LanguageChunker(ABC):
    language: str

    @abstractmethod
    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        raise NotImplementedError

    def build_chunk(
        self,
        chunk_text: str,
        chunk_type: str,
        start_line: int | None = None,
        end_line: int | None = None,
        symbol_name: str | None = None,
    ) -> RagEvidenceChunkDraftDTO:
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
    return (
        chunk_type.startswith("python_")
        and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )
