# Classifies Python AST nodes into chunk types.
import ast
from typing import TypeAlias

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
PythonChunkNode: TypeAlias = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


# python chunk classification DTO
class PythonChunkClassificationDTO(BaseModel):
    """파일 경로와 AST 의미 분석 결과를 하나로 모아 최종 chunk_type 결정을 돕는다."""

    node_kind: str
    path_role: str | None = None
    semantic_role: str | None = None
    is_api_route: bool = False
    is_placeholder: bool = False
    is_test: bool = False


# python chunk type classifier
class PythonChunkClassifier:
    """Python AST 노드를 SQL/RAG 검색에 쓸 수 있는 안정적인 chunk_type으로 분류한다."""

    def detect_chunk_type(self, node: PythonChunkNode, path: str) -> str:
        """분류 DTO를 거치되 호출자는 최종 문자열 타입만 받게 한다."""

        classification = self.classify(node, path)
        return self.resolve_chunk_type(classification)

    def classify(self, node: PythonChunkNode, path: str) -> PythonChunkClassificationDTO:
        """경로 역할, 상속/필드 의미, 데코레이터를 따로 판단해 분류 근거를 보존한다."""

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
        """API route, placeholder, test 같은 우선순위가 높은 의미를 먼저 반영한다."""

        if classification.is_api_route:
            return "python_api_route"

        if classification.is_placeholder:
            return "python_placeholder"

        if classification.is_test:
            return build_python_chunk_type("test", classification.node_kind)

        role = classification.semantic_role or classification.path_role
        return build_python_chunk_type(role, classification.node_kind)


# default classifier
DEFAULT_PYTHON_CHUNK_CLASSIFIER = PythonChunkClassifier()


# legacy helper functions
def detect_python_chunk_type(node: PythonChunkNode, path: str) -> str:
    """기존 함수형 호출부를 깨지 않기 위한 호환용 진입점."""

    return DEFAULT_PYTHON_CHUNK_CLASSIFIER.detect_chunk_type(node, path)


def classify_python_chunk(node: PythonChunkNode, path: str) -> PythonChunkClassificationDTO:
    """테스트나 디버깅에서 chunk_type 결정 근거까지 확인할 때 사용한다."""

    return DEFAULT_PYTHON_CHUNK_CLASSIFIER.classify(node, path)


def detect_python_node_kind(node: PythonChunkNode) -> str:
    """class, function, async function을 chunk_type suffix로 쓸 짧은 값으로 바꾼다."""

    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, ast.AsyncFunctionDef):
        return "async_function"
    return "function"


def detect_python_path_role(path: str) -> str | None:
    """파일명과 폴더명을 보고 service, schema, repository 같은 역할 힌트를 찾는다."""

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


def detect_python_semantic_role(node: PythonChunkNode) -> str | None:
    """클래스 상속과 필드 선언을 보고 schema/model 같은 코드 의미를 추정한다."""

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
    """검색 필터에 쓰기 쉬운 python_{role}_{kind} 규칙의 타입 문자열을 만든다."""

    if role is None:
        return f"python_{node_kind}"

    return f"python_{role}_{node_kind}"


def is_test_node(node: PythonChunkNode, path_role: str | None) -> bool:
    """테스트 폴더, test_ 함수명, pytest 데코레이터 중 하나라도 맞으면 테스트로 본다."""

    if path_role == "test":
        return True

    if node.name.startswith("test_"):
        return True

    decorator_names = detect_decorator_names(node)
    return bool(decorator_names & PYTHON_TEST_DECORATOR_NAMES)


def has_api_route_decorator(node: PythonChunkNode) -> bool:
    """FastAPI/라우터 데코레이터가 붙은 함수인지 확인해 API 근거로 분류한다."""

    return any(is_api_route_decorator(decorator) for decorator in node.decorator_list)


def detect_class_base_names(node: ast.ClassDef) -> set[str]:
    """상속 기반 의미 분석을 위해 클래스 base expression을 문자열 집합으로 만든다."""

    base_names = set()

    for base in node.bases:
        base_name = ast_expression_name(base)
        if base_name:
            base_names.add(normalize_ast_name(base_name))

    return base_names


def has_model_field_assignment(node: ast.ClassDef) -> bool:
    """SQLAlchemy 모델처럼 컬럼 필드를 선언한 클래스를 model 역할로 추정한다."""

    for statement in node.body:
        value = field_assignment_value(statement)
        if is_named_call(value, PYTHON_MODEL_FIELD_CALL_NAMES):
            return True

    return False


def is_api_route_decorator(decorator: ast.expr) -> bool:
    """HTTP method 이름과 path 인자를 가진 데코레이터만 API route로 인정한다."""

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


def detect_decorator_names(node: PythonChunkNode) -> set[str]:
    """pytest fixture처럼 decorator 이름만으로 의미를 판단해야 할 때 사용한다."""

    decorator_names = set()

    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        decorator_name = ast_expression_name(target)
        if decorator_name:
            decorator_names.add(normalize_ast_name(decorator_name))

    return decorator_names


def is_named_call(value: ast.expr | None, call_names: set[str]) -> bool:
    """AST 값이 특정 함수 호출인지 확인해 ORM 필드 선언 등을 판별한다."""

    if not isinstance(value, ast.Call):
        return False

    call_name = ast_expression_name(value.func)
    return last_name(call_name) in call_names


def ast_expression_name(node: ast.expr) -> str:
    """Name/Attribute AST를 dotted 문자열로 바꿔 decorator와 base class 비교에 사용한다."""

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent_name = ast_expression_name(node.value)
        if parent_name:
            return f"{parent_name}.{node.attr}"
        return node.attr

    return ""


def normalize_ast_name(name: str) -> str:
    """대소문자나 공백 차이 때문에 의미 비교가 흔들리지 않게 정규화한다."""

    return name.replace(" ", "").lower()


def last_name(name: str) -> str:
    """module.attr 형태에서도 마지막 식별자만 비교할 수 있게 한다."""

    return normalize_ast_name(name).split(".")[-1]


def has_placeholder_body(node: PythonChunkNode) -> bool:
    """아직 구현되지 않은 pass/빈 return 함수는 실제 구현 근거와 분리한다."""

    return bool(node.body) and all(
        isinstance(statement, ast.Pass)
        or (
            isinstance(statement, ast.Return)
            and statement.value is None
        )
        for statement in node.body
    )


def field_assignment_value(statement: ast.stmt) -> ast.expr | None:
    """클래스 본문에서 필드 선언의 오른쪽 값을 꺼내 모델 필드 호출인지 검사하게 한다."""

    if isinstance(statement, ast.Assign):
        return statement.value

    if isinstance(statement, ast.AnnAssign):
        return statement.value

    return None
