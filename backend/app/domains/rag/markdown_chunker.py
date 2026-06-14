from dataclasses import dataclass

from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.chunking_base import LanguageChunker
from app.domains.rag.schema import RagEvidenceChunkDraftDTO


@dataclass
class MarkdownSection:
    text: str
    heading: str
    start_line: int
    end_line: int


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


def build_markdown_sections(
    lines: list[str],
    default_heading: str,
) -> list[MarkdownSection]:
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
