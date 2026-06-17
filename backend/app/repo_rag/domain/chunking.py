import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pipeline.router import RepoSnapshot, RetrievalChunk
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
SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".pyi": "python",
    ".md": "markdown",
    ".markdown": "markdown",
    ".ts": "code",
    ".tsx": "code",
    ".js": "code",
    ".jsx": "code",
    ".sql": "sql",
    ".json": "config",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".txt": "text",
    ".pdf": "pdf",
}
NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES = {"python_parse_error", "python_symbol_part"}
SUMMARY_CHUNK_CHARS = 1200


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
            return self._build_plain_text_chunks(file_context, content_text, "python_parse_error")

        lines = content_text.splitlines()
        nested: list[ChunkDraft | list[ChunkDraft]] = [
            self._build_symbol_chunk(file_context, lines, node)
            for node in ast.walk(tree)
            if _is_python_chunk_node(node)
        ]
        chunks = _flatten_chunks(nested)

        if chunks:
            chunks.insert(0, _file_summary_draft(file_context, "python_file_summary"))
            chunks.sort(key=lambda chunk: chunk.start_line or 0)
            return chunks

        return self._build_plain_text_chunks(file_context, content_text, "python_file")

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
            return self._build_plain_text_chunks(file_context, chunk_text, "python_symbol_part")

        return ChunkDraft(
            text=chunk_text,
            chunk_type=self.classifier.detect_chunk_type(node, file_context.path),
            start_line=start_line,
            end_line=end_line,
            symbol_name=getattr(node, "name", None),
        )

    def _build_plain_text_chunks(
        self,
        file_context: FileContext,
        content_text: str,
        chunk_type: str,
    ) -> list[ChunkDraft]:
        return _split_with_offsets(file_context, content_text, chunk_type, self.text_splitter_service)


@dataclass(slots=True)
class MarkdownSection:
    text: str
    heading: str
    heading_path: list[str]
    start_line: int
    end_line: int


class MarkdownChunker(LanguageChunker):
    language = "markdown"

    def __init__(
        self,
        text_splitter_service: TextSplitterService | None = None,
    ) -> None:
        self.text_splitter_service = text_splitter_service or DEFAULT_TEXT_SPLITTER_SERVICE

    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        lines = file_context.content.splitlines()
        sections = build_markdown_sections(lines, default_heading=file_context.path)

        drafts: list[ChunkDraft] = []
        for section in sections:
            parts = self.text_splitter_service.split(section.text)
            if len(parts) <= 1:
                drafts.append(_markdown_draft(section, section.text))
                continue
            for index, part in enumerate(parts, start=1):
                drafts.append(
                    _markdown_draft(
                        section,
                        part,
                        chunk_type="markdown_section_part",
                        symbol_name=f"{section.heading} part {index}",
                    )
                )
        return drafts


class SplitTextChunker(LanguageChunker):
    language = "text"

    def __init__(
        self,
        *,
        language: str,
        chunk_type: str,
        text_splitter_service: TextSplitterService | None = None,
    ) -> None:
        self.language = language
        self.chunk_type = chunk_type
        self.text_splitter_service = text_splitter_service or DEFAULT_TEXT_SPLITTER_SERVICE

    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        return _split_with_offsets(file_context, file_context.content, self.chunk_type, self.text_splitter_service)


class CodeLikeChunker(SplitTextChunker):
    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        drafts = [_file_summary_draft(file_context, f"{self.language}_file_summary")]
        drafts.extend(super().build_chunks(file_context))
        return drafts


class PdfChunker(LanguageChunker):
    language = "pdf"

    def __init__(
        self,
        text_splitter_service: TextSplitterService | None = None,
    ) -> None:
        self.text_splitter_service = text_splitter_service or DEFAULT_TEXT_SPLITTER_SERVICE

    def build_chunks(self, file_context: FileContext) -> list[ChunkDraft]:
        drafts: list[ChunkDraft] = []
        pages = _split_pdf_pages(file_context.content)
        for page_number, page_text in pages:
            page_context = FileContext(
                repository=file_context.repository,
                path=file_context.path,
                commit_sha=file_context.commit_sha,
                content_hash=file_context.content_hash,
                content=page_text,
                language=file_context.language,
                source_type=file_context.source_type,
            )
            for draft in _split_with_offsets(
                page_context,
                page_text,
                "pdf_page_section",
                self.text_splitter_service,
            ):
                draft.page = page_number
                draft.heading_path = _detect_heading_path(page_text)
                drafts.append(draft)
        return drafts


class LanguageChunkerRegistry:
    def __init__(self, chunkers: list[LanguageChunker]) -> None:
        self.chunkers = {chunker.language: chunker for chunker in chunkers}

    def get(self, language: str) -> LanguageChunker | None:
        return self.chunkers.get(language)


DEFAULT_CHUNKER_REGISTRY = LanguageChunkerRegistry(
    chunkers=[
        PythonChunker(text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE),
        MarkdownChunker(text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE),
        CodeLikeChunker(
            language="code",
            chunk_type="code_text_section",
            text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE,
        ),
        CodeLikeChunker(
            language="sql",
            chunk_type="sql_section",
            text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE,
        ),
        SplitTextChunker(
            language="config",
            chunk_type="config_section",
            text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE,
        ),
        SplitTextChunker(
            language="text",
            chunk_type="text_section",
            text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE,
        ),
        PdfChunker(text_splitter_service=DEFAULT_TEXT_SPLITTER_SERVICE),
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
                source_id=None,
                format=file_context.language,
                chunk_type=draft.chunk_type,
                symbol_name=draft.symbol_name,
                heading_path=draft.heading_path,
                page=draft.page,
                start_line=draft.start_line,
                end_line=draft.end_line,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
                content_hash=file_context.content_hash,
                parent_chunk_id=draft.parent_chunk_id,
                prev_chunk_id=draft.prev_chunk_id,
                next_chunk_id=draft.next_chunk_id,
                language=file_context.language,
            )
        )

    return _link_neighbor_chunks(evidence_chunks)


def build_markdown_sections(lines: list[str], default_heading: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    current_heading = default_heading
    current_heading_path = [default_heading]
    current_start = 1
    current_lines: list[str] = []
    heading_stack: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if is_markdown_heading(line) and current_lines:
            sections.append(
                MarkdownSection(
                    text="\n".join(current_lines),
                    heading=current_heading,
                    heading_path=current_heading_path,
                    start_line=current_start,
                    end_line=line_number - 1,
                )
            )
            current_lines = []
            current_start = line_number

        if is_markdown_heading(line):
            level, heading = parse_markdown_heading(line)
            current_heading = heading or default_heading
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(current_heading)
            current_heading_path = heading_stack.copy()

        current_lines.append(line)

    if current_lines:
        sections.append(
            MarkdownSection(
                text="\n".join(current_lines),
                heading=current_heading,
                heading_path=current_heading_path,
                start_line=current_start,
                end_line=len(lines) or 1,
            )
        )

    return sections


def is_markdown_heading(line: str) -> bool:
    return parse_markdown_heading(line)[0] > 0


def parse_markdown_heading(line: str) -> tuple[int, str]:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if match is None:
        return 0, ""
    return len(match.group(1)), match.group(2).strip()


def is_direct_implementation_chunk_type(chunk_type: str) -> bool:
    return (
        chunk_type.startswith("python_") and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )


def _flatten_chunks(items: list[ChunkDraft | list[ChunkDraft]]) -> list[ChunkDraft]:
    chunks: list[ChunkDraft] = []
    for item in items:
        if isinstance(item, list):
            chunks.extend(item)
        else:
            chunks.append(item)
    return chunks


def _file_summary_draft(file_context: FileContext, chunk_type: str) -> ChunkDraft:
    lines = file_context.content.splitlines()
    text = file_context.content[:SUMMARY_CHUNK_CHARS]
    return ChunkDraft(
        text=text,
        chunk_type=chunk_type,
        start_line=1 if lines else None,
        end_line=min(len(lines), text.count("\n") + 1) if lines else None,
        start_offset=0,
        end_offset=len(text),
        symbol_name="file",
    )


def _markdown_draft(
    section: MarkdownSection,
    text: str,
    *,
    chunk_type: str = "markdown_section",
    symbol_name: str | None = None,
) -> ChunkDraft:
    return ChunkDraft(
        text=text,
        chunk_type=chunk_type,
        start_line=section.start_line,
        end_line=section.end_line,
        symbol_name=symbol_name or section.heading,
        heading_path=section.heading_path,
    )


def _split_with_offsets(
    file_context: FileContext,
    content_text: str,
    chunk_type: str,
    text_splitter_service: TextSplitterService,
) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    cursor = 0
    for chunk_text in text_splitter_service.split(content_text):
        start_offset = content_text.find(chunk_text, cursor)
        if start_offset < 0:
            start_offset = cursor
        end_offset = start_offset + len(chunk_text)
        cursor = end_offset
        drafts.append(
            ChunkDraft(
                text=chunk_text,
                chunk_type=chunk_type,
                start_line=_line_for_offset(content_text, start_offset),
                end_line=_line_for_offset(content_text, max(start_offset, end_offset - 1)),
                start_offset=start_offset,
                end_offset=end_offset,
                heading_path=_detect_heading_path(chunk_text),
            )
        )
    return drafts


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset)) + 1


def _split_pdf_pages(text: str) -> list[tuple[int, str]]:
    if "\f" in text:
        return [(index, page.strip()) for index, page in enumerate(text.split("\f"), start=1) if page.strip()]
    return [(1, text)]


def _detect_heading_path(text: str) -> list[str] | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if is_markdown_heading(stripped):
            return [parse_markdown_heading(stripped)[1]]
        if len(stripped) <= 80 and not stripped.endswith((".", ",", ";")):
            return [stripped]
        break
    return None


def _link_neighbor_chunks(chunks: list[RetrievalChunk]) -> list[RetrievalChunk]:
    linked: list[RetrievalChunk] = []
    for index, chunk in enumerate(chunks):
        linked.append(
            chunk.model_copy(
                update={
                    "prev_chunk_id": chunks[index - 1].id if index > 0 else chunk.prev_chunk_id,
                    "next_chunk_id": (
                        chunks[index + 1].id if index + 1 < len(chunks) else chunk.next_chunk_id
                    ),
                }
            )
        )
    return linked


def _is_python_chunk_node(node: ast.AST) -> bool:
    return isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
