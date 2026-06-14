import ast
from typing import TypeAlias, TypeGuard

from app.github.api.schema import GitHubFileSnapshotDTO
from app.rag.api.schema import RagEvidenceChunkDraftDTO
from app.rag.domain.chunking_base import LanguageChunker, TextSplitter
from app.rag.domain.python_classifier import PythonChunkClassifier

MAX_SYMBOL_CHARS = 4000
PythonChunkNode: TypeAlias = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


class PythonChunker(LanguageChunker):
    """Python 파일을 class/function 중심으로 나눠 코드 구조가 검색 근거에 남게 한다."""

    language = "python"

    def __init__(
        self,
        classifier: PythonChunkClassifier,
        text_splitter: TextSplitter,
    ) -> None:
        self.classifier = classifier
        self.text_splitter = text_splitter

    def build_chunks(
        self,
        file_snapshot: GitHubFileSnapshotDTO,
    ) -> list[RagEvidenceChunkDraftDTO]:
        """AST 파싱이 되면 symbol 단위로, 실패하면 일반 텍스트 조각으로 fallback한다."""

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
        node: PythonChunkNode,
    ) -> RagEvidenceChunkDraftDTO | list[RagEvidenceChunkDraftDTO]:
        """AST node의 원본 줄 범위를 잘라 청크로 만들고, 너무 길면 재분할한다."""

        start_line = node.lineno
        end_line = node.end_lineno or start_line
        chunk_text = "\n".join(lines[start_line - 1 : end_line])

        if len(chunk_text) > MAX_SYMBOL_CHARS:
            return self.build_plain_text_chunks(chunk_text, "python_symbol_part")

        return self.build_chunk(
            chunk_text=chunk_text,
            start_line=start_line,
            end_line=end_line,
            symbol_name=node.name,
            chunk_type=self.classifier.detect_chunk_type(node, file_snapshot.path),
        )

    def build_plain_text_chunks(
        self,
        content_text: str,
        chunk_type: str,
    ) -> list[RagEvidenceChunkDraftDTO]:
        """구조화가 어렵거나 너무 긴 코드를 검색 가능한 일반 텍스트 청크로 나눈다."""

        return [
            self.build_chunk(chunk_text=chunk_text, chunk_type=chunk_type)
            for chunk_text in self.text_splitter.split(content_text)
        ]


def is_python_chunk_node(node: ast.AST) -> TypeGuard[PythonChunkNode]:
    """RAG 근거로 삼을 수 있는 최상위 코드 symbol인지 타입을 좁힌다."""

    return isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))


def flatten_chunks(
    chunks: list[RagEvidenceChunkDraftDTO | list[RagEvidenceChunkDraftDTO]],
) -> list[RagEvidenceChunkDraftDTO]:
    """긴 symbol 재분할 때문에 섞인 단일 청크와 목록 청크를 하나의 목록으로 편다."""

    flattened_chunks: list[RagEvidenceChunkDraftDTO] = []

    for chunk in chunks:
        if isinstance(chunk, list):
            flattened_chunks.extend(chunk)
        else:
            flattened_chunks.append(chunk)

    return flattened_chunks
