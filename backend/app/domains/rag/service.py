import ast

from app.common.identity import hash_text
from app.common.validation import require_value
from app.domains.github.schema import GitHubFileSnapshotDTO
from app.domains.rag.schema import (
    RagChunkMetadataDTO,
    RagEvidenceChunkDraftDTO,
    RagEvidenceChunkDTO,
)
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_LANGUAGES = {"python", "markdown"}
NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES = {
    "python_parse_error",
    "python_symbol_part",
}
PYTHON_PATH_ROLE_KEYWORDS = {
    "model": {"entity", "entities", "model", "models"},
    "schema": {"dto", "dtos", "schema", "schemas", "serializer", "serializers"},
    "repository": {"dao", "repository", "repositories"},
    "service": {"service", "services", "usecase", "usecases"},
    "router": {"api", "endpoint", "endpoints", "router", "routers"},
    "test": {"spec", "specs", "test", "tests"},
}
PYTHON_HTTP_METHOD_DECORATORS = {
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
}
PYTHON_ROUTE_DECORATOR_NAMES = {
    "route",
}
PYTHON_TEST_DECORATOR_NAMES = {
    "fixture",
    "mark.parametrize",
    "pytest.fixture",
    "pytest.mark.parametrize",
}
PYTHON_SCHEMA_BASE_NAMES = {
    "basemodel",
    "pydantic.basemodel",
}
PYTHON_MODEL_BASE_NAMES = {
    "declarativebase",
    "sqlmodel",
}
PYTHON_MODEL_FIELD_CALL_NAMES = {
    "column",
    "mapped_column",
    "relationship",
}
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
MAX_SYMBOL_CHARS = 4000
CHUNK_HASH_LENGTH = 16

# RAG의 흐름을 조립하는 곳.
"""
1. board 데이터를 가져온다
2. board + detail + task를 하나의 임베딩용 텍스트로 만든다

2. github.service에서 받은 텍스트를 chunk
3. 텍스트가 길면 chunk로 나눈다
4. repository에 저장하라고 넘긴다
5. 검색 요청이 오면 repository에서 관련 chunk를 검색한다
"""


# TODO: board + detail + task를 하나의 임베딩용 텍스트로
def embedding_from_db():
    return "A"


# chunk text
def text_splitter(merged_text):
    split_texts = RecursiveCharacterTextSplitter(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    text_list = split_texts.split_text(merged_text)
    return text_list


# create
# TODO: repository에 저장하라고 넘김 == 벡터DB


# get
# TODO: 검색 요청이 오면 repository==vector db에서 관련 chunk를 검색


## embedding the chunked text
def create_embedding_model():
    return OpenAIEmbeddings(model="text-embedding-3-large")


def build_minimal_evidence_chunks(
    file_snapshot: GitHubFileSnapshotDTO,
) -> list[RagEvidenceChunkDTO]:
    validate_file_snapshot(file_snapshot)

    language = file_snapshot.language
    content_text = file_snapshot.content_text

    if language == "python":
        chunks = chunk_python_snapshot(file_snapshot, content_text)
    elif language == "markdown":
        chunks = chunk_markdown_snapshot(file_snapshot, content_text)
    else:
        return []

    evidence_chunks: list[RagEvidenceChunkDTO] = []

    for index, chunk in enumerate(chunks):
        chunk_hash = build_chunk_hash(file_snapshot, chunk)
        evidence_chunks.append(
            RagEvidenceChunkDTO(
                id=build_chunk_id(file_snapshot, chunk_hash),
                chunk_hash=chunk_hash,
                citation=build_chunk_citation(file_snapshot, chunk),
                chunk_index=index,
                path=file_snapshot.path,
                commit_sha=file_snapshot.commit_sha,
                language=language,
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


# helpers

def validate_file_snapshot(file_snapshot: GitHubFileSnapshotDTO) -> None:
    require_value(file_snapshot.path, "file_snapshot.path")
    require_value(file_snapshot.commit_sha, "file_snapshot.commit_sha")
    require_value(file_snapshot.source_type, "file_snapshot.source_type")
    require_value(file_snapshot.content_text, "file_snapshot.content_text")
    require_value(file_snapshot.language, "file_snapshot.language")


def chunk_python_snapshot(
    file_snapshot: GitHubFileSnapshotDTO,
    content_text: str,
) -> list[RagEvidenceChunkDraftDTO]:
    try:
        tree = ast.parse(content_text)
    except SyntaxError:
        return chunk_plain_text(content_text, chunk_type="python_parse_error")

    lines = content_text.splitlines()
    chunks = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)
        chunk_text = "\n".join(lines[start_line - 1:end_line])

        if len(chunk_text) > MAX_SYMBOL_CHARS:
            chunks.extend(chunk_plain_text(chunk_text, chunk_type="python_symbol_part"))
            continue

        chunks.append(
            build_chunk(
                chunk_text=chunk_text,
                start_line=start_line,
                end_line=end_line,
                symbol_name=node.name,
                chunk_type=detect_python_chunk_type(node, file_snapshot.path),
            )
        )

    if chunks:
        chunks.sort(key=lambda chunk: chunk.start_line or 0)
        return chunks

    return chunk_plain_text(content_text, chunk_type="python_file")


def chunk_markdown_snapshot(
    file_snapshot: GitHubFileSnapshotDTO,
    content_text: str,
) -> list[RagEvidenceChunkDraftDTO]:
    lines = content_text.splitlines()
    chunks = []
    current_heading = file_snapshot.path
    current_start = 1
    current_lines: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("#") and current_lines:
            chunks.append(
                build_chunk(
                    chunk_text="\n".join(current_lines),
                    start_line=current_start,
                    end_line=line_number - 1,
                    symbol_name=current_heading,
                    chunk_type="markdown_section",
                )
            )
            current_lines = []
            current_start = line_number

        if line.startswith("#"):
            current_heading = line.lstrip("#").strip() or file_snapshot.path

        current_lines.append(line)

    if current_lines:
        chunks.append(
            build_chunk(
                chunk_text="\n".join(current_lines),
                start_line=current_start,
                end_line=len(lines) or 1,
                symbol_name=current_heading,
                chunk_type="markdown_section",
            )
        )

    return chunks


def chunk_plain_text(
    content_text: str,
    chunk_type: str,
) -> list[RagEvidenceChunkDraftDTO]:
    return [
        build_chunk(
            chunk_text=chunk_text,
            start_line=None,
            end_line=None,
            symbol_name=None,
            chunk_type=chunk_type,
        )
        for chunk_text in text_splitter(content_text)
    ]


def build_chunk(
    chunk_text: str,
    start_line: int | None,
    end_line: int | None,
    symbol_name: str | None,
    chunk_type: str,
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


def build_chunk_hash(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    raw_identity = "\0".join(
        [
            file_snapshot.path,
            file_snapshot.content_hash,
            chunk.chunk_type,
            chunk.symbol_name or "",
            chunk.chunk_text,
        ]
    )
    return hash_text(raw_identity)[:CHUNK_HASH_LENGTH]


def build_chunk_id(file_snapshot: GitHubFileSnapshotDTO, chunk_hash: str) -> str:
    return f"{file_snapshot.path}@{file_snapshot.commit_sha}:{chunk_hash}"


def build_chunk_citation(
    file_snapshot: GitHubFileSnapshotDTO,
    chunk: RagEvidenceChunkDraftDTO,
) -> str:
    if chunk.start_line is None:
        return file_snapshot.citation

    line_range = str(chunk.start_line)
    if chunk.end_line is not None and chunk.end_line != chunk.start_line:
        line_range = f"{chunk.start_line}-{chunk.end_line}"

    return f"{file_snapshot.path}:{line_range}@{file_snapshot.commit_sha}"


def detect_python_chunk_type(node: ast.AST, path: str) -> str:
    node_kind = detect_python_node_kind(node)
    path_role = detect_python_path_role(path)

    if has_api_route_decorator(node):
        return "python_api_route"

    if has_placeholder_body(node):
        return "python_placeholder"

    if is_test_node(node, path_role):
        return build_python_chunk_type("test", node_kind)

    semantic_role = detect_python_semantic_role(node)
    return build_python_chunk_type(semantic_role or path_role, node_kind)


def detect_python_node_kind(node: ast.AST) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async_function"
    return "function"


def detect_python_path_role(path: str) -> str | None:
    normalized_path = path.replace("\\", "/").lower()
    path_parts = [part for part in normalized_path.split("/") if part]
    file_name = path_parts[-1] if path_parts else normalized_path
    file_stem = file_name.removesuffix(".py")
    candidates = {*path_parts, file_stem}

    if file_stem.startswith("test_") or file_stem.endswith("_test"):
        return "test"

    for role, keywords in PYTHON_PATH_ROLE_KEYWORDS.items():
        if candidates & keywords:
            return role

    return None


def detect_python_semantic_role(node: ast.AST) -> str | None:
    if not isinstance(node, ast.ClassDef):
        return None

    base_names = detect_class_base_names(node)

    if base_names & PYTHON_SCHEMA_BASE_NAMES:
        return "schema"

    if base_names & PYTHON_MODEL_BASE_NAMES:
        return "model"

    if has_model_field_assignment(node):
        return "model"

    return None


def build_python_chunk_type(role: str | None, node_kind: str) -> str:
    if role is None:
        return f"python_{node_kind}"

    return f"python_{role}_{node_kind}"


def is_test_node(node: ast.AST, path_role: str | None) -> bool:
    if path_role == "test":
        return True

    node_name = getattr(node, "name", "")
    if isinstance(node_name, str) and node_name.startswith("test_"):
        return True

    decorator_names = detect_decorator_names(node)
    return bool(decorator_names & PYTHON_TEST_DECORATOR_NAMES)


def has_api_route_decorator(node: ast.AST) -> bool:
    decorators = getattr(node, "decorator_list", [])
    return any(
        is_api_route_decorator(decorator)
        for decorator in decorators
    )


def detect_class_base_names(node: ast.ClassDef) -> set[str]:
    base_names = set()

    for base in node.bases:
        base_name = ast_expression_name(base)
        if base_name:
            base_names.add(normalize_ast_name(base_name))

    return base_names


def has_model_field_assignment(node: ast.ClassDef) -> bool:
    for statement in node.body:
        value = getattr(statement, "value", None)
        if is_named_call(value, PYTHON_MODEL_FIELD_CALL_NAMES):
            return True

    return False


def is_api_route_decorator(decorator: ast.AST) -> bool:
    if not isinstance(decorator, ast.Call):
        return False

    decorator_name = ast_expression_name(decorator.func)
    route_decorator_names = PYTHON_HTTP_METHOD_DECORATORS | PYTHON_ROUTE_DECORATOR_NAMES
    if last_name(decorator_name) not in route_decorator_names:
        return False

    return bool(
        decorator.args
        and isinstance(decorator.args[0], ast.Constant)
        and isinstance(decorator.args[0].value, str)
        and decorator.args[0].value.startswith("/")
    )


def detect_decorator_names(node: ast.AST) -> set[str]:
    decorators = getattr(node, "decorator_list", [])
    decorator_names = set()

    for decorator in decorators:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        decorator_name = ast_expression_name(target)
        if decorator_name:
            decorator_names.add(normalize_ast_name(decorator_name))

    return decorator_names


def is_named_call(value: ast.AST | None, call_names: set[str]) -> bool:
    if not isinstance(value, ast.Call):
        return False

    call_name = ast_expression_name(value.func)
    return last_name(call_name) in call_names


def ast_expression_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent_name = ast_expression_name(node.value)
        if parent_name:
            return f"{parent_name}.{node.attr}"
        return node.attr

    return ""


def normalize_ast_name(name: str) -> str:
    return name.replace(" ", "").lower()


def last_name(name: str) -> str:
    return normalize_ast_name(name).split(".")[-1]


def is_direct_implementation_chunk_type(chunk_type: str) -> bool:
    return (
        chunk_type.startswith("python_")
        and chunk_type not in NON_DIRECT_IMPLEMENTATION_CHUNK_TYPES
    )


def has_placeholder_body(node: ast.AST) -> bool:
    body = getattr(node, "body", [])
    return bool(body) and all(
        isinstance(statement, ast.Pass)
        or (
            isinstance(statement, ast.Return)
            and statement.value is None
        )
        for statement in body
    )
