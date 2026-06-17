"""코드에서 정적으로(AST) 사실 골격을 추출해 UML/ERD 생성을 보강하는 하이브리드 유틸.

원리:
- UML: Python 클래스의 이름/상속/메서드/속성을 AST로 추출한다(사실).
- ERD: SQLAlchemy/Django ORM 모델과 SQL ``CREATE TABLE`` 에서 엔티티/컬럼/FK를 추출한다.

쓰임:
- ``*_facts_text`` 는 LLM 프롬프트에 "정적 추출된 사실"로 주입해 환각을 줄이고 정확도를
  높이는 데 쓴다(ChatOpenAIArtifactGenerator).
- ``build_*_mermaid`` 는 LLM 키가 없을 때 이 사실만으로 결정론 Mermaid를 직접 생성한다
  (최소 Python/ORM 한정). 추출 실패 시 None을 돌려 호출부가 골격 폴백으로 전환한다.

순수 표준 라이브러리(ast/re)만 사용하며, 외부 키가 필요 없다.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from app.notebooks.domain.artifact_ports import ArtifactContext

_PY_EXTS = (".py", ".pyi")
_JS_EXTS = (".js", ".jsx", ".ts", ".tsx")
# ORM 베이스로 자주 쓰이는 이름(상속 기반 모델 판별).
_MODEL_BASE_HINTS = ("Base", "Model", "DeclarativeBase", "SQLModel")
# 컬럼 정의 호출 이름.
_COLUMN_CALLS = ("Column", "mapped_column")
MAX_UML_NODES = 90
_UML_LAYER_ORDER = (
    ("entry", "Entry / API / UI"),
    ("application", "Application / Service"),
    ("domain", "Domain / Contract"),
    ("infrastructure", "Infrastructure / Adapter"),
    ("data", "Data / Schema / Model"),
    ("config", "Config / Runtime"),
    ("tests", "Tests"),
    ("other", "Other"),
)


# ── UML: 클래스 골격 ────────────────────────────────────────────────


@dataclass(slots=True)
class ClassInfo:
    name: str
    path: str | None = None
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


def _name_of(node: ast.AST) -> str:
    """식 노드에서 식별자/점표기 이름을 최대한 복원한다."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _python_class_references(node: ast.ClassDef, bases: list[str]) -> list[str]:
    refs: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            refs.append(child.id)
        elif isinstance(child, ast.Attribute):
            refs.append(child.attr)
        elif isinstance(child, (ast.arg, ast.AnnAssign)) and child.annotation is not None:
            refs.extend(_annotation_names(child.annotation))
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.returns is not None:
            refs.extend(_annotation_names(child.returns))
    ignored = {node.name, *bases}
    return [ref for ref in _dedupe(refs) if ref not in ignored]


def _annotation_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.append(child.id)
        elif isinstance(child, ast.Attribute):
            names.append(child.attr)
    return names


def extract_python_classes(text: str, *, path: str | None = None) -> list[ClassInfo]:
    """파이썬 소스에서 클래스(상속/공개 메서드/속성)를 추출한다.

    문법 오류 파일은 빈 목록으로 흡수한다(에러를 던지지 않는다).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    classes: list[ClassInfo] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        info = ClassInfo(name=node.name, path=path)
        for base in node.bases:
            name = _name_of(base)
            if name:
                info.bases.append(name)
        for member in node.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 던더/프라이빗은 다이어그램 노이즈라 제외.
                if not member.name.startswith("__"):
                    info.methods.append(member.name)
            elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                info.attributes.append(member.target.id)
            elif isinstance(member, ast.Assign):
                for target in member.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("__"):
                        info.attributes.append(target.id)
        info.references.extend(_python_class_references(node, info.bases))
        classes.append(info)
    return classes


def _python_classes(contexts: list[ArtifactContext]) -> list[ClassInfo]:
    out: list[ClassInfo] = []
    for ctx in contexts:
        if ctx.path and ctx.path.lower().endswith(_PY_EXTS):
            out.extend(extract_python_classes(ctx.text, path=ctx.path))
    return out


_JS_CLASS_RE = re.compile(
    r"\b(?:export\s+)?class\s+([A-Za-z_]\w*)(?:\s+extends\s+([A-Za-z_][\w.]*))?"
    r"\s*\{(?P<body>.*?)\n\}",
    re.DOTALL,
)
_JS_INTERFACE_RE = re.compile(
    r"\b(?:export\s+)?(?:interface|type)\s+([A-Za-z_]\w*)[^{=]*[={]\s*(?P<body>.*?)\n\}",
    re.DOTALL,
)
_JS_METHOD_RE = re.compile(r"^\s*(?:async\s+)?([A-Za-z_]\w*)\s*\(", re.MULTILINE)
_JS_FIELD_RE = re.compile(r"^\s*(?:readonly\s+)?([A-Za-z_]\w*)\??\s*[:=]", re.MULTILINE)
_JS_TYPE_REF_RE = re.compile(r"\b[A-Z][A-Za-z0-9_]+\b")


def extract_javascript_classes(text: str, *, path: str | None = None) -> list[ClassInfo]:
    """TS/JS 소스에서 클래스/인터페이스 골격을 간단히 추출한다."""
    classes: list[ClassInfo] = []
    for match in _JS_CLASS_RE.finditer(text):
        body = match.group("body")
        info = ClassInfo(name=match.group(1), path=path)
        if match.group(2):
            info.bases.append(match.group(2).split(".")[-1])
        info.methods.extend(
            name
            for name in _JS_METHOD_RE.findall(body)
            if name not in {"if", "for", "while", "switch"}
        )
        info.attributes.extend(_JS_FIELD_RE.findall(body))
        ignored = {info.name, *info.bases}
        info.references.extend(ref for ref in _JS_TYPE_REF_RE.findall(body) if ref not in ignored)
        classes.append(info)

    for match in _JS_INTERFACE_RE.finditer(text):
        body = match.group("body")
        fields = _JS_FIELD_RE.findall(body)
        if fields:
            classes.append(
                ClassInfo(
                    name=match.group(1),
                    path=path,
                    attributes=fields,
                    references=_JS_TYPE_REF_RE.findall(body),
                )
            )
    return classes


def _code_classes(contexts: list[ArtifactContext]) -> list[ClassInfo]:
    out: list[ClassInfo] = []
    for ctx in contexts:
        path = (ctx.path or "").lower()
        if path.endswith(_PY_EXTS):
            out.extend(extract_python_classes(ctx.text, path=ctx.path))
        elif path.endswith(_JS_EXTS):
            out.extend(extract_javascript_classes(ctx.text, path=ctx.path))
    return _merge_classes(out)


def uml_facts_text(contexts: list[ArtifactContext]) -> str:
    """LLM 프롬프트에 주입할 클래스 사실 목록(없으면 빈 문자열)."""
    classes = _code_classes(contexts)
    if not classes:
        return ""
    lines: list[str] = []
    for c in classes:
        base = (" extends " + ", ".join(c.bases)) if c.bases else ""
        methods = ", ".join(_dedupe(c.methods)) or "-"
        attrs = ", ".join(_dedupe(c.attributes)) or "-"
        lines.append(f"- {c.name}{base} | methods: {methods} | attrs: {attrs}")
    return "\n".join(lines)


def build_uml_mermaid(contexts: list[ArtifactContext]) -> str | None:
    """추출한 클래스로 Mermaid classDiagram을 만든다."""
    classes = _code_classes(contexts)
    if not classes:
        return None
    names = {c.name for c in classes}
    relations = _class_relations(classes, names)
    classes = _select_uml_classes(classes, relations)
    visible = {c.name for c in classes}
    relations = {
        (src, dst, label)
        for src, dst, label in relations
        if src in visible and dst in visible and src != dst
    }

    lines = [
        "classDiagram",
        "    direction TB",
        "    %% 선택한 소스에서 추출한 클래스/인터페이스의 속성, 메서드, 상속, 참조 관계입니다.",
    ]

    current_layer: str | None = None
    sorted_classes = sorted(
        classes,
        key=lambda item: (_layer_rank(_layer_for_path(item.path)), item.name),
    )
    for item in sorted_classes:
        layer = _layer_for_path(item.path)
        if layer != current_layer:
            lines.append(f"    %% {_layer_label(layer)}")
            current_layer = layer
        lines.extend(_class_diagram_block(item))

    for src, dst, label in sorted(relations):
        src_id = _safe_id(src)
        dst_id = _safe_id(dst)
        if label == "extends":
            lines.append(f"    {dst_id} <|-- {src_id} : 상속")
        else:
            lines.append(f"    {src_id} ..> {dst_id} : 참조")
    return "\n".join(lines) + "\n"


def _class_relations(
    classes: list[ClassInfo],
    names: set[str],
) -> set[tuple[str, str, str]]:
    relations: set[tuple[str, str, str]] = set()
    for item in classes:
        for base in item.bases:
            normalized = base.split(".")[-1]
            if normalized in names and normalized != item.name:
                relations.add((item.name, normalized, "extends"))
        for ref in item.references:
            normalized = ref.split(".")[-1]
            if normalized in names and normalized != item.name:
                relations.add((item.name, normalized, "uses"))
    return relations


def _select_uml_classes(
    classes: list[ClassInfo],
    relations: set[tuple[str, str, str]],
) -> list[ClassInfo]:
    if len(classes) <= MAX_UML_NODES:
        return classes
    connected = {src for src, _, _ in relations} | {dst for _, dst, _ in relations}
    ranked = sorted(
        classes,
        key=lambda item: (
            item.name not in connected,
            _layer_rank(_layer_for_path(item.path)),
            item.path or "",
            item.name,
        ),
    )
    return ranked[:MAX_UML_NODES]


def _layer_rank(layer: str) -> int:
    for index, (key, _label) in enumerate(_UML_LAYER_ORDER):
        if key == layer:
            return index
    return len(_UML_LAYER_ORDER)


def _layer_label(layer: str) -> str:
    labels = {
        "entry": "진입점/API/UI",
        "application": "애플리케이션/서비스",
        "domain": "도메인/계약",
        "infrastructure": "인프라/어댑터",
        "data": "데이터/스키마",
        "config": "설정/런타임",
        "tests": "테스트",
        "other": "기타",
    }
    return labels.get(layer, "기타")


def _layer_for_path(path: str | None) -> str:
    lowered = (path or "").lower()
    if "/test" in lowered or lowered.startswith("test") or "/tests/" in lowered:
        return "tests"
    if _has_path_part(lowered, ("api", "router", "routes", "endpoint", "controller")):
        return "entry"
    if _has_path_part(lowered, ("application", "service", "usecase", "use_case", "agent")):
        return "application"
    if _has_path_part(
        lowered,
        ("domain", "ports", "contract", "record", "records", "type", "types"),
    ):
        return "domain"
    if _has_path_part(lowered, ("infrastructure", "adapter", "client", "store", "repository")):
        return "infrastructure"
    if _has_path_part(lowered, ("model", "models", "schema", "schemas", "migration", "db")):
        return "data"
    if _has_path_part(lowered, ("config", "settings", "dependency", "dependencies", "assembly")):
        return "config"
    return "other"


def _has_path_part(path: str, parts: tuple[str, ...]) -> bool:
    tokens = set(re.split(r"[/_.-]+", path))
    return any(part in tokens for part in parts)


def _class_diagram_block(item: ClassInfo) -> list[str]:
    ident = _safe_id(item.name)
    attrs = [attr for attr in _dedupe(item.attributes) if not attr.startswith("_")][:8]
    methods = [method for method in _dedupe(item.methods) if not method.startswith("_")][:10]
    if not attrs and not methods:
        return [f"    class {ident}"]
    lines = [f"    class {ident} {{"]
    for attr in attrs:
        lines.append(f"        +{_safe_member(attr)}")
    for method in methods:
        lines.append(f"        +{_safe_member(method)}()")
    lines.append("    }")
    return lines


# ── ERD: ORM 모델 / SQL 골격 ────────────────────────────────────────


@dataclass(slots=True)
class Entity:
    name: str
    class_name: str | None = None
    columns: list[str] = field(default_factory=list)
    # (대상 엔티티, 라벨) 관계. FK 기반.
    relations: list[tuple[str, str]] = field(default_factory=list)


def _looks_like_model(node: ast.ClassDef) -> bool:
    for base in node.bases:
        name = _name_of(base)
        if name in _MODEL_BASE_HINTS or name.endswith(_MODEL_BASE_HINTS):
            return True
    return False


def _fk_target(call: ast.Call) -> str | None:
    """Column(...) 호출 인자에서 ForeignKey("table.col") 의 대상 테이블을 찾는다."""
    if _name_of(call.func) == "ForeignKey":
        for fk_arg in call.args:
            if isinstance(fk_arg, ast.Constant) and isinstance(fk_arg.value, str):
                return fk_arg.value.split(".")[0]
    for arg in call.args:
        if isinstance(arg, ast.Call) and _name_of(arg.func) == "ForeignKey":
            for fk_arg in arg.args:
                if isinstance(fk_arg, ast.Constant) and isinstance(fk_arg.value, str):
                    return fk_arg.value.split(".")[0]
    return None


def _column_from(member: ast.stmt) -> tuple[str, str | None] | None:
    """클래스 본문 한 줄이 컬럼 정의면 (컬럼명, FK대상|None)을 돌려준다."""
    target_name: str | None = None
    value: ast.expr | None = None
    if isinstance(member, ast.Assign) and len(member.targets) == 1:
        target = member.targets[0]
        if isinstance(target, ast.Name):
            target_name = target.id
            value = member.value
    elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
        target_name = member.target.id
        value = member.value
    if target_name is None or not isinstance(value, ast.Call):
        return None
    if _name_of(value.func) not in _COLUMN_CALLS:
        return None
    return target_name, _fk_target(value)


def extract_models(text: str) -> list[Entity]:
    """파이썬 ORM 모델(엔티티/컬럼/FK)을 추출한다."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    model_nodes: list[tuple[ast.ClassDef, str | None]] = []
    class_to_table: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        tablename: str | None = None
        is_model = _looks_like_model(node)
        for member in node.body:
            if isinstance(member, ast.Assign):
                for target in member.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(member.value, ast.Constant)
                    ):
                        tablename = str(member.value.value)
        if is_model or tablename:
            model_nodes.append((node, tablename))
            class_to_table[node.name] = tablename or node.name

    entities: list[Entity] = []
    for node, tablename in model_nodes:
        columns: list[str] = []
        fks: list[str] = []
        relationships: list[str] = []
        is_model = True
        for member in node.body:
            column = _column_from(member)
            if column is not None:
                is_model = True
                columns.append(column[0])
                if column[1]:
                    fks.append(column[1])
            rel_target = _relationship_target(member)
            if rel_target:
                relationships.append(class_to_table.get(rel_target, rel_target))
        if not is_model:
            continue
        entity = Entity(name=tablename or node.name, class_name=node.name, columns=columns)
        for target in _dedupe(fks):
            entity.relations.append((target, "FK"))
        for target in _dedupe(relationships):
            entity.relations.append((target, "relationship"))
        entities.append(entity)
    return entities


def _relationship_target(member: ast.stmt) -> str | None:
    value: ast.expr | None = None
    if (isinstance(member, ast.Assign) and len(member.targets) == 1) or isinstance(
        member,
        ast.AnnAssign,
    ):
        value = member.value
    if not isinstance(value, ast.Call) or _name_of(value.func) != "relationship":
        return None
    for arg in value.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        name = _name_of(arg)
        if name:
            return name
    return None


_CREATE_TABLE_RE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"`']?(\w+)", re.IGNORECASE)
_SQL_FK_RE = re.compile(r"references\s+[\"`']?(\w+)", re.IGNORECASE)
_SQL_COLUMN_RE = re.compile(r"^\s*[\"`']?([A-Za-z_]\w*)[\"`']?\s+[A-Za-z]", re.MULTILINE)
_SQL_NON_COLUMN_WORDS = {
    "alter",
    "check",
    "constraint",
    "create",
    "foreign",
    "key",
    "on",
    "primary",
    "references",
    "unique",
    "where",
}


def extract_sql_tables(text: str) -> list[Entity]:
    """SQL CREATE TABLE 에서 엔티티명과 FK 참조 테이블을 추출한다(간이)."""
    entities: list[Entity] = []
    for match in _CREATE_TABLE_RE.finditer(text):
        name = match.group(1)
        block = _create_table_body(text, match.end())
        rels = [(t, "FK") for t in _dedupe(_SQL_FK_RE.findall(block))]
        columns = [
            col
            for col in _dedupe(_SQL_COLUMN_RE.findall(block))
            if col.lower() not in _SQL_NON_COLUMN_WORDS
        ]
        entities.append(Entity(name=name, columns=columns, relations=rels))
    return entities


def _create_table_body(text: str, start: int) -> str:
    open_index = text.find("(", start)
    if open_index < 0:
        return ""
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index]
    return text[open_index + 1 :]


def _all_entities(contexts: list[ArtifactContext]) -> list[Entity]:
    out: list[Entity] = []
    for ctx in contexts:
        path = (ctx.path or "").lower()
        if path.endswith(_PY_EXTS):
            out.extend(extract_models(ctx.text))
        elif path.endswith(".sql"):
            out.extend(extract_sql_tables(ctx.text))
    return _merge_entities(out)


def erd_facts_text(contexts: list[ArtifactContext]) -> str:
    """LLM 프롬프트에 주입할 엔티티/관계 사실(없으면 빈 문자열)."""
    entities = _all_entities(contexts)
    if not entities:
        return ""
    lines: list[str] = []
    for e in entities:
        cols = ", ".join(_dedupe(e.columns)) or "-"
        lines.append(f"- {e.name} | columns: {cols}")
        for target, label in e.relations:
            lines.append(f"    -> {e.name} {label} {target}")
    return "\n".join(lines)


def build_erd_mermaid(contexts: list[ArtifactContext]) -> str | None:
    """추출한 엔티티로 결정론 erDiagram을 만든다(엔티티가 없으면 None)."""
    entities = _all_entities(contexts)
    if not entities:
        return None
    entities = _with_relation_placeholders(entities)
    names = {e.name for e in entities}
    lines = ["erDiagram"]
    for e in entities:
        ident = _safe_id(e.name)
        cols = _dedupe(e.columns)
        if not cols:
            lines.append(f"    {ident} {{")
            lines.append("        string id")
            lines.append("    }")
            continue
        lines.append(f"    {ident} {{")
        for col in cols:
            lines.append(f"        string {_safe_member(col)}")
        lines.append("    }")
    # 관계(FK): 자식 }o--|| 부모.
    for e in entities:
        for target, label in e.relations:
            if target in names and target != e.name:
                lines.append(f"    {_safe_id(e.name)} }}o--|| {_safe_id(target)} : {label}")
    return "\n".join(lines) + "\n"


def _with_relation_placeholders(entities: list[Entity]) -> list[Entity]:
    names = {entity.name for entity in entities}
    additions: list[Entity] = []
    for entity in entities:
        for target, _label in entity.relations:
            if target and target not in names:
                additions.append(Entity(name=target, columns=["id"]))
                names.add(target)
    return [*entities, *additions]


# ── 공통 헬퍼 ───────────────────────────────────────────────────────


def _dedupe(items: list[str]) -> list[str]:
    """순서를 유지하며 중복 제거."""
    return list(dict.fromkeys(items))


def _merge_classes(classes: list[ClassInfo]) -> list[ClassInfo]:
    merged: dict[str, ClassInfo] = {}
    for item in classes:
        if item.name not in merged:
            merged[item.name] = ClassInfo(name=item.name, path=item.path)
        target = merged[item.name]
        if target.path is None and item.path:
            target.path = item.path
        target.bases.extend(item.bases)
        target.methods.extend(item.methods)
        target.attributes.extend(item.attributes)
        target.references.extend(item.references)
    for item in merged.values():
        item.bases = _dedupe(item.bases)
        item.methods = _dedupe(item.methods)
        item.attributes = _dedupe(item.attributes)
        item.references = _dedupe(item.references)
    return list(merged.values())


def _merge_entities(entities: list[Entity]) -> list[Entity]:
    merged: dict[str, Entity] = {}
    for item in entities:
        if item.name not in merged:
            merged[item.name] = Entity(name=item.name, class_name=item.class_name)
        target = merged[item.name]
        if target.class_name is None and item.class_name:
            target.class_name = item.class_name
        target.columns.extend(item.columns)
        target.relations.extend(item.relations)
    for item in merged.values():
        item.columns = _dedupe(item.columns)
        item.relations = list(dict.fromkeys(item.relations))
    return list(merged.values())


def _safe_id(name: str) -> str:
    """Mermaid 식별자로 안전한 문자만 남긴다(영숫자/언더스코어)."""
    cleaned = re.sub(r"[^0-9A-Za-z_]", "_", name)
    return cleaned or "Node"


def _safe_member(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]", "_", name)
