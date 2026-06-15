import ast

from pydantic import BaseModel

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


class PythonChunkClassificationDTO(BaseModel):
    node_kind: str
    path_role: str | None = None
    semantic_role: str | None = None
    is_api_route: bool = False
    is_placeholder: bool = False
    is_test: bool = False


class PythonChunkClassifier:
    def detect_chunk_type(self, node: ast.AST, path: str) -> str:
        classification = self.classify(node, path)
        return self.resolve_chunk_type(classification)

    def classify(self, node: ast.AST, path: str) -> PythonChunkClassificationDTO:
        path_role = detect_python_path_role(path)
        return PythonChunkClassificationDTO(
            node_kind=detect_python_node_kind(node),
            path_role=path_role,
            semantic_role=detect_python_semantic_role(node),
            is_api_route=has_api_route_decorator(node),
            is_placeholder=has_placeholder_body(node),
            is_test=is_test_node(node, path_role),
        )

    def resolve_chunk_type(self, classification: PythonChunkClassificationDTO) -> str:
        if classification.is_api_route:
            return "python_api_route"

        if classification.is_placeholder:
            return "python_placeholder"

        if classification.is_test:
            return build_python_chunk_type("test", classification.node_kind)

        role = classification.semantic_role or classification.path_role
        return build_python_chunk_type(role, classification.node_kind)


DEFAULT_PYTHON_CHUNK_CLASSIFIER = PythonChunkClassifier()


def detect_python_chunk_type(node: ast.AST, path: str) -> str:
    return DEFAULT_PYTHON_CHUNK_CLASSIFIER.detect_chunk_type(node, path)


def classify_python_chunk(node: ast.AST, path: str) -> PythonChunkClassificationDTO:
    return DEFAULT_PYTHON_CHUNK_CLASSIFIER.classify(node, path)


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
    return any(is_api_route_decorator(decorator) for decorator in decorators)


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
    route_names = PYTHON_HTTP_METHOD_DECORATORS | PYTHON_ROUTE_DECORATOR_NAMES
    if last_name(decorator_name) not in route_names:
        return False

    return bool(
        decorator.args
        and isinstance(decorator.args[0], ast.Constant)
        and isinstance(decorator.args[0].value, str)
        and decorator.args[0].value.startswith("/")
    )


def detect_decorator_names(node: ast.AST) -> set[str]:
    decorator_names = set()

    for decorator in getattr(node, "decorator_list", []):
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


def has_placeholder_body(node: ast.AST) -> bool:
    body = getattr(node, "body", [])
    return bool(body) and all(
        isinstance(statement, ast.Pass)
        or (isinstance(statement, ast.Return) and statement.value is None)
        for statement in body
    )
