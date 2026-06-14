import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.common.validation import require_value
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.chunk_identity import (
    build_chunk_citation,
    build_chunk_hash,
    build_chunk_id,
)
from app.domains.rag.python_classifier import PythonChunkClassifier
from app.domains.rag.schema import (
    RagChunkMetadataDTO,
    RagEvidenceChunkDraftDTO,
    RagEvidenceChunkDTO,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
MAX_SYMBOL_CHARS = 4000
TEXT_SPLIT_SEPARATORS = ["\n\n", "\n", " ", ""]
NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES = {
    "python_parse_error",
    "python_symbol_part",
}


class TextSplitterService:
    def split(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=len,
            separators=TEXT_SPLIT_SEPARATORS,
        )
        return splitter.split_text(text)


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


class PythonChunker(LanguageChunker):
    language = "python"

    def __init__(
        self,
        classifier: PythonChunkClassifier | None = None,
        text_splitter_service: TextSplitterService | None = None,
    ) -> None:
        self.classifier = classifier or PythonChunkClassifier()
        self.text_splitter_service = text_splitter_service or TextSplitterService()

    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        content_text = file_snapshot.content_text

        try:
            tree = ast.parse(content_text)
        except SyntaxError:
            return self.build_plain_text_chunks(content_text, "python_parse_error")

        lines = content_text.splitlines()
        chunks = [
            self.build_symbol_chunk(file_snapshot, lines, node)
            for node in ast.walk(tree)
            if is_python_chunk_node(node)
        ]
        chunks = flatten_chunks(chunks)

        if chunks:
            chunks.sort(key=lambda chunk: chunk.start_line or 0)
            return chunks

        return self.build_plain_text_chunks(content_text, "python_file")

    def build_symbol_chunk(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
        lines: list[str],
        node: ast.AST,
    ) -> RagEvidenceChunkDraftDTO | list[RagEvidenceChunkDraftDTO]:
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        chunk_text = "\n".join(lines[start_line - 1:end_line])

        if len(chunk_text) > MAX_SYMBOL_CHARS:
            return self.build_plain_text_chunks(chunk_text, "python_symbol_part")

        return self.build_chunk(
            chunk_text=chunk_text,
            start_line=start_line,
            end_line=end_line,
            symbol_name=getattr(node, "name", None),
            chunk_type=self.classifier.detect_chunk_type(node, file_snapshot.path),
        )

    def build_plain_text_chunks(
        self,
        content_text: str,
        chunk_type: str,
    ) -> list[RagEvidenceChunkDraftDTO]:
        return [
            self.build_chunk(chunk_text=chunk_text, chunk_type=chunk_type)
            for chunk_text in self.text_splitter_service.split(content_text)
        ]


class MarkdownChunker(LanguageChunker):
    language = "markdown"

    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        lines = file_snapshot.content_text.splitlines()
        sections = build_markdown_sections(lines, default_heading=file_snapshot.path)

        return [
            self.build_chunk(
                chunk_text=section.text,
                start_line=section.start_line,
                end_line=section.end_line,
                symbol_name=section.heading,
                chunk_type="markdown_section",
            )
            for section in sections
        ]


class LanguageChunkerRegistry:
    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
        return self.chunkers.get(language)


@dataclass
class MarkdownSection:
    text: str
    heading: str
    start_line: int
    end_line: int


DEFAULT_TEXT_SPLITTER_SERVICE = TextSplitterService()
DEFAULT_CHUNKER_REGISTRY = LanguageChunkerRegistry(
    chunkers=[
        PythonChunker(text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE),
        MarkdownChunker(),
    ]
)


def build_minimal_evidence_chunks(
    file_snapshot: GitHubFileSnapshotDTO,
    chunker_registry: LanguageChunkerRegistry = DEFAULT_CHUNKER_REGISTRY,
) -> list[RagEvidenceChunkDTO]:
    validate_file_snapshot(file_snapshot)

    chunker = chunker_registry.get(file_snapshot.language)
    if chunker is None:
        return []

    draft_chunks = chunker.build_chunks(file_snapshot)
    return build_evidence_chunks(file_snapshot, draft_chunks)


def build_evidence_chunks(
    file_snapshot: GitHubFileSnapshotDTO,
    draft_chunks: list[RagEvidenceChunkDraftDTO],
) -> list[RagEvidenceChunkDTO]:
    evidence_chunks: list[RagEvidenceChunkDTO] = []

    for index, chunk in enumerate(draft_chunks):
        chunk_hash = build_chunk_hash(file_snapshot, chunk)
        evidence_chunks.append(
            RagEvidenceChunkDTO(
                id=build_chunk_id(file_snapshot, chunk_hash),
                chunk_hash=chunk_hash,
                citation=build_chunk_citation(file_snapshot, chunk),
                chunk_index=index,
                path=file_snapshot.path,
                commit_sha=file_snapshot.commit_sha,
                language=file_snapshot.language,
                source_type=file_snapshot.source_type,
                chunk_text=chunk.chunk_text,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol_name=chunk.symbol_name,
                chunk_type=chunk.chunk_type,
                metadata=chunk.metadata,
            )
        )

    return evidence_chunks


def validate_file_snapshot(file_snapshot: GitHubFileSnapshotDTO) -> None:
    require_value(file_snapshot.path, "file_snapshot.path")
    require_value(file_snapshot.commit_sha, "file_snapshot.commit_sha")
    require_value(file_snapshot.source_type, "file_snapshot.source_type")
    require_value(file_snapshot.content_text, "file_snapshot.content_text")
    require_value(file_snapshot.language, "file_snapshot.language")


def build_markdown_sections(
    lines: list[str],
    default_heading: str,
) -> list[MarkdownSection]:
    sections = []
    current_heading = default_heading
    current_start = 1
    current_lines: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if is_markdown_heading(line) and current_lines:
            sections.append(
                MarkdownSection(
                    text="\n".join(current_lines),
                    heading=current_heading,
                    start_line=current_start,
                    end_line=line_number - 1,
                )
            )
            current_lines = []
            current_start = line_number

        if is_markdown_heading(line):
            current_heading = line.lstrip("#").strip() or default_heading

        current_lines.append(line)

    if current_lines:
        sections.append(
            MarkdownSection(
                text="\n".join(current_lines),
                heading=current_heading,
                start_line=current_start,
                end_line=len(lines) or 1,
            )
        )

    return sections


def text_splitter(merged_text: str) -> list[str]:
    return DEFAULT_TEXT_SPLITTER_SERVICE.split(merged_text)


def is_python_chunk_node(node: ast.AST) -> bool:
    return isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))


def flatten_chunks(
    chunks: list[RagEvidenceChunkDraftDTO | list[RagEvidenceChunkDraftDTO]],
) -> list[RagEvidenceChunkDraftDTO]:
    flattened_chunks = []

    for chunk in chunks:
        if isinstance(chunk, list):
            flattened_chunks.extend(chunk)
        else:
            flattened_chunks.append(chunk)

    return flattened_chunks


def is_markdown_heading(line: str) -> bool:
    return line.startswith("#")


def is_direct_implementation_chunk_type(chunk_type: str) -> bool:
    return (
        chunk_type.startswith("python_")
        and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )
