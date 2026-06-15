import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pipeline.api.schemas import RepoSnapshot, RetrievalChunk
from app.repo_rag.api.schemas import RepoFileChange
from app.repo_rag.domain.chunk_identity import (
    ChunkDraft,
    FileContext,
    build_chunk_citation,
    build_chunk_hash,
    build_chunk_id,
)
from app.repo_rag.domain.identity import file_hash
from app.repo_rag.domain.python_classifier import PythonChunkClassifier
from app.repo_rag.domain.text_splitter import DEFAULT_TEXT_SPLITTER_SERVICE, TextSplitterService

MAX_SYMBOL_CHARS = 4000
CHANGED_STATUSES = {"added", "modified"}
SUPPORTED_LANGUAGES = {".py": "python", ".md": "markdown"}
NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES = {"python_parse_error", "python_symbol_part"}


def detect_language(path: str) -> str | None:
    normalized_path = path.lower()
    for extension, language in SUPPORTED_LANGUAGES.items():
        if normalized_path.endswith(extension):
            return language
    return None


class LanguageChunker(ABC):
    language: str

    @abstractmethod
    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        raise NotImplementedError


class PythonChunker(LanguageChunker):
    language = "python"

    def __init__(
        self,
        classifier: PythonChunkClassifier | None = None,
        text_splitter_service: TextSplitterService | None = None,
    ) -> None:
        self.classifier = classifier or PythonChunkClassifier()
        self.text_splitter_service = text_splitter_service or DEFAULT_TEXT_SPLITTER_SERVICE

    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        content_text = file_context.content

        try:
            tree = ast.parse(content_text)
        except SyntaxError:
            return self._build_plain_text_chunks(content_text, "python_parse_error")

        lines = content_text.splitlines()
        nested: list[ChunkDraft | list[ChunkDraft]] = [
            self._build_symbol_chunk(file_context, lines, node)
            for node in ast.walk(tree)
            if _is_python_chunk_node(node)
        ]
        chunks = _flatten_chunks(nested)

        if chunks:
            chunks.sort(key=lambda chunk: chunk.start_line or 0)
            return chunks

        return self._build_plain_text_chunks(content_text, "python_file")

    def _build_symbol_chunk(
        self,
        file_context: FileContext,
        lines: list[str],
        node: ast.AST,
    ) -> ChunkDraft | list[ChunkDraft]:
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        chunk_text = "\n".join(lines[start_line - 1 : end_line])

        if len(chunk_text) > MAX_SYMBOL_CHARS:
            return self._build_plain_text_chunks(chunk_text, "python_symbol_part")

        return ChunkDraft(
            text=chunk_text,
            chunk_type=self.classifier.detect_chunk_type(node, file_context.path),
            start_line=start_line,
            end_line=end_line,
            symbol_name=getattr(node, "name", None),
        )

    def _build_plain_text_chunks(self, content_text: str, chunk_type: str) -> list[ChunkDraft]:
        return [
            ChunkDraft(text=chunk_text, chunk_type=chunk_type)
            for chunk_text in self.text_splitter_service.split(content_text)
        ]


@dataclass(slots=True)
class MarkdownSection:
    text: str
    heading: str
    start_line: int
    end_line: int


class MarkdownChunker(LanguageChunker):
    language = "markdown"

    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        lines = file_context.content.splitlines()
        sections = build_markdown_sections(lines, default_heading=file_context.path)

        return [
            ChunkDraft(
                text=section.text,
                chunk_type="markdown_section",
                start_line=section.start_line,
                end_line=section.end_line,
                symbol_name=section.heading,
            )
            for section in sections
        ]


class LanguageChunkerRegistry:
    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
        return self.chunkers.get(language)


DEFAULT_CHUNKER_REGISTRY = LanguageChunkerRegistry(
    chunkers=[
        PythonChunker(text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE),
        MarkdownChunker(),
    ]
)


class ChunkingService:
    def __init__(
        self,
        chunker_registry: LanguageChunkerRegistry = DEFAULT_CHUNKER_REGISTRY,
    ) -> None:
        self.chunker_registry = chunker_registry

    def chunk_changed_files(
        self,
        snapshot: RepoSnapshot,
        changes: list[RepoFileChange],
    ) -> list[RetrievalChunk]:
        changed_paths = {change.path for change in changes if change.status in CHANGED_STATUSES}
        chunks: list[RetrievalChunk] = []

        for file in snapshot.files:
            if file.path not in changed_paths:
                continue
            if not file.content.strip():
                continue

            language = detect_language(file.path)
            if language is None:
                continue

            chunker = self.chunker_registry.get(language)
            if chunker is None:
                continue

            file_context = FileContext(
                repository=snapshot.repository,
                path=file.path,
                commit_sha=snapshot.commit_sha,
                content_hash=file_hash(file),
                content=file.content,
                language=language,
            )
            drafts = chunker.build_chunks(file_context)
            chunks.extend(build_evidence_chunks(file_context, drafts))

        return chunks


def build_evidence_chunks(
    file_context: FileContext,
    drafts: list[ChunkDraft],
) -> list[RetrievalChunk]:
    evidence_chunks: list[RetrievalChunk] = []

    for draft in drafts:
        if not draft.text.strip():
            continue

        chunk_hash = build_chunk_hash(file_context, draft)
        evidence_chunks.append(
            RetrievalChunk(
                id=build_chunk_id(file_context, chunk_hash),
                source_path=file_context.path,
                text=draft.text,
                citation=build_chunk_citation(file_context, draft),
                chunk_type=draft.chunk_type,
                symbol_name=draft.symbol_name,
                start_line=draft.start_line,
                end_line=draft.end_line,
                language=file_context.language,
            )
        )

    return evidence_chunks


def build_markdown_sections(lines: list[str], default_heading: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
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


def is_markdown_heading(line: str) -> bool:
    return line.startswith("#")


def is_direct_implementation_chunk_type(chunk_type: str) -> bool:
    return (
        chunk_type.startswith("python_") and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )


def _is_python_chunk_node(node: ast.AST) -> bool:
    return isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))


def _flatten_chunks(chunks: list[ChunkDraft | list[ChunkDraft]]) -> list[ChunkDraft]:
    flattened: list[ChunkDraft] = []
    for chunk in chunks:
        if isinstance(chunk, list):
            flattened.extend(chunk)
        else:
            flattened.append(chunk)
    return flattened
