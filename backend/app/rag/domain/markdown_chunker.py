from dataclasses import dataclass

from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDraftDTO
from app.rag.domain.chunking_base import LanguageChunker


@dataclass
class MarkdownSection:
    """Markdown heading 단위로 잘라낸 텍스트와 원본 줄 범위를 함께 보관한다."""

    text: str
    heading: str
    start_line: int
    end_line: int


class MarkdownChunker(LanguageChunker):
    """문서 구조가 검색 근거로 남도록 Markdown을 heading section 단위로 나눈다."""

    language = "markdown"

    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        """파일 내용을 section으로 나누고 각 heading을 symbol_name으로 보존한다."""

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
    """heading이 나타날 때마다 이전 section을 닫아 줄 번호가 있는 문서 조각을 만든다."""

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
    """MVP에서는 #으로 시작하는 줄을 문서 section 경계로 사용한다."""

    return line.startswith("#")
