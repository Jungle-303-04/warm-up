"""산출물 생성기(LlmArtifactGenerator) 어댑터.

두 종류의 어댑터를 제공한다.

- DeterministicArtifactGenerator: 외부 키 없이 동작하는 결정론 생성기.
  - dependency: 파이썬 파일들의 import 문을 파싱해 모듈 간 의존 그래프를 Mermaid
    flowchart로 생성한다(키 불필요).
  - uml/erd/change_summary: 빈 다이어그램 + "LLM 키가 필요합니다" 주석 골격을 반환한다
    (에러가 아니라 명시적 폴백).
- ChatOpenAIArtifactGenerator: llm_provider="openai"이고 키가 있을 때 LangChain
  ChatOpenAI로 타입별 system 프롬프트를 실행한다. LLM 호출/파싱 실패 시
  DeterministicArtifactGenerator로 안전하게 폴백한다(런타임 에러 0).

타입→system 프롬프트는 레지스트리(_SYSTEM_PROMPTS)로 두어 새 에이전트를 쉽게
추가할 수 있게 한다. 무거운 의존성(langchain)은 함수 내 지연 import 한다.
"""

from __future__ import annotations

import ast
import re

from app.notebooks.domain.artifact_ports import ArtifactContext, GenerationRequest
from app.notebooks.domain.artifact_records import ArtifactType

# 컨텍스트 토큰 과다 방지를 위한 상한(어댑터에서 자른다).
MAX_CONTEXT_CHARS = 12000

# LLM 키가 없을 때 골격에 들어가는 안내 주석.
_NEED_KEY_NOTE = "LLM 키가 필요합니다"


class DeterministicArtifactGenerator:
    """키 없이 동작하는 결정론 생성기.

    dependency는 import 파싱으로 실제 그래프를 만들고, 나머지 타입은 골격을 돌려준다.
    """

    def generate(self, request: GenerationRequest) -> str:
        if request.type == "dependency":
            return build_dependency_mermaid(request.contexts)
        return _skeleton(request.type)


class ChatOpenAIArtifactGenerator:
    """LangChain ChatOpenAI 기반 생성기.

    타입별 system 프롬프트 + 컨텍스트로 Mermaid/마크다운만 출력하도록 유도한다.
    dependency는 (키가 있어도) 결정론 그래프가 더 정확하므로 결정론 경로를 사용한다.
    실패 시 결정론 폴백으로 전환한다(에러를 밖으로 던지지 않는다).
    """

    def __init__(self, chat_model: object) -> None:
        self._chat_model = chat_model
        self._fallback = DeterministicArtifactGenerator()

    def generate(self, request: GenerationRequest) -> str:
        # dependency는 코드 사실 기반이라 결정론 생성이 더 신뢰도가 높다.
        if request.type == "dependency":
            return self._fallback.generate(request)

        try:
            prompt = _build_prompt(request)
            response = self._chat_model.invoke(prompt)  # type: ignore[attr-defined]
            content = _coerce_text(getattr(response, "content", response))
            content = _strip_code_fence(content).strip()
            if content:
                return content
        except Exception:
            # 네트워크/파싱/키 오류 등은 폴백으로 흡수.
            pass
        return self._fallback.generate(request)


# --- 타입별 system 프롬프트 레지스트리(새 에이전트 추가 지점) ---

_SYSTEM_PROMPTS: dict[ArtifactType, str] = {
    "uml": (
        "당신은 코드로부터 UML 클래스 다이어그램을 만드는 보조자입니다. "
        "주어진 코드 컨텍스트의 클래스/메서드/속성과 상속·구성 관계를 분석해 "
        "Mermaid `classDiagram` 한 개만 출력하세요. 설명·코드펜스 없이 다이어그램 본문만."
    ),
    "erd": (
        "당신은 코드/스키마로부터 ERD를 만드는 보조자입니다. "
        "엔티티와 관계(1:N 등)를 분석해 Mermaid `erDiagram` 한 개만 출력하세요. "
        "설명·코드펜스 없이 다이어그램 본문만."
    ),
    "change_summary": (
        "당신은 코드/문서 변경을 요약하는 보조자입니다. "
        "주어진 컨텍스트의 핵심을 한국어 마크다운으로 간결히 요약하세요. "
        "필요하면 Mermaid 다이어그램을 마크다운에 포함해도 됩니다."
    ),
}


def _build_prompt(request: GenerationRequest) -> str:
    system = _SYSTEM_PROMPTS.get(
        request.type,
        "주어진 컨텍스트를 한국어로 요약하세요.",
    )
    context = _format_contexts(request.contexts)
    return f"{system}\n\n[컨텍스트]\n{context}"


def _format_contexts(contexts: list[ArtifactContext]) -> str:
    if not contexts:
        return "(컨텍스트 없음)"
    parts: list[str] = []
    used = 0
    for ctx in contexts:
        where = ctx.path or ctx.source_title
        block = f"# {where}\n{ctx.text}"
        if used + len(block) > MAX_CONTEXT_CHARS:
            remaining = MAX_CONTEXT_CHARS - used
            if remaining > 0:
                parts.append(block[:remaining])
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def _skeleton(artifact_type: ArtifactType) -> str:
    """LLM 키가 없을 때의 골격(빈 다이어그램 + 안내 주석)."""

    if artifact_type == "uml":
        return (
            "classDiagram\n"
            f"    %% {_NEED_KEY_NOTE}: llm_provider=openai 와 OPENAI_API_KEY 설정 시 "
            "코드 기반 클래스 다이어그램이 생성됩니다.\n"
            "    class Placeholder {\n"
            "    }\n"
        )
    if artifact_type == "erd":
        return (
            "erDiagram\n"
            f"    %% {_NEED_KEY_NOTE}: llm_provider=openai 와 OPENAI_API_KEY 설정 시 "
            "코드/스키마 기반 ERD가 생성됩니다.\n"
            '    PLACEHOLDER {\n'
            "        string id\n"
            "    }\n"
        )
    if artifact_type == "change_summary":
        return (
            "## 변경 요약\n\n"
            f"> {_NEED_KEY_NOTE}: llm_provider=openai 와 OPENAI_API_KEY 를 설정하면 "
            "선택한 소스 기반 요약이 생성됩니다.\n"
        )
    # note 등 그 외 타입은 빈 골격.
    return f"%% {_NEED_KEY_NOTE}\n"


# --- dependency: 파이썬 import 파싱 → Mermaid flowchart(결정론) ---


def build_dependency_mermaid(contexts: list[ArtifactContext]) -> str:
    """파이썬 파일들의 import 문을 파싱해 모듈 의존 그래프를 Mermaid flowchart로 만든다.

    - 각 컨텍스트의 path를 모듈명으로 변환(.py 제거, '/'→'.')하고, import 대상 중
      이 그래프에 존재하는 모듈(내부 의존)만 엣지로 그린다.
    - 외부 의존(표준/서드파티)은 노드가 없으므로 자연히 제외된다.
    - import가 전혀 없으면 노드만 나열한 그래프를 돌려준다(에러 아님).
    """

    # path가 있는 파이썬 파일만 대상으로 모듈 목록을 만든다.
    modules: dict[str, str] = {}  # module_name -> node_id
    file_modules: list[tuple[str, str]] = []  # (module_name, source_text)
    for ctx in contexts:
        path = ctx.path
        if not path or not path.endswith(".py"):
            continue
        module = _path_to_module(path)
        if not module:
            continue
        modules.setdefault(module, _node_id(module))
        file_modules.append((module, ctx.text))

    if not modules:
        return (
            "flowchart TD\n"
            "    %% 의존 그래프를 만들 파이썬 소스를 찾지 못했습니다. "
            "(.py 파일 소스를 선택해 주세요.)\n"
            "    none[no python sources]\n"
        )

    edges: set[tuple[str, str]] = set()
    for module, text in file_modules:
        for imported in _extract_imports(text, current_module=module):
            target = _resolve_internal(imported, modules)
            if target is not None and target != module:
                edges.add((module, target))

    lines = ["flowchart TD"]
    # 노드 선언(결정론을 위해 정렬).
    for module in sorted(modules):
        node = modules[module]
        lines.append(f'    {node}["{module}"]')
    # 엣지(정렬).
    for src, dst in sorted(edges):
        lines.append(f"    {modules[src]} --> {modules[dst]}")
    return "\n".join(lines) + "\n"


def _path_to_module(path: str) -> str:
    cleaned = path.strip().lstrip("./")
    if cleaned.endswith(".py"):
        cleaned = cleaned[: -len(".py")]
    if cleaned.endswith("/__init__"):
        cleaned = cleaned[: -len("/__init__")]
    parts = [p for p in cleaned.split("/") if p and p != "."]
    return ".".join(parts)


def _node_id(module: str) -> str:
    # Mermaid 노드 id는 영숫자/언더스코어만 안전하게.
    return "n_" + re.sub(r"[^0-9A-Za-z_]", "_", module)


def _extract_imports(source_text: str, *, current_module: str) -> list[str]:
    """소스에서 import된 모듈명을 추출한다(ast 우선, 실패 시 정규식 폴백)."""

    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return _extract_imports_regex(source_text)

    imports: list[str] = []
    parent_parts = current_module.split(".")[:-1]  # 현재 모듈의 패키지 경로
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level and node.level > 0:
                # 상대 import: 현재 패키지 기준으로 절대화.
                base = parent_parts[: len(parent_parts) - (node.level - 1)]
                module = ".".join([*base, module]) if module else ".".join(base)
            if module:
                imports.append(module)
            for alias in node.names:
                # from pkg import submod 형태에서 submod도 후보로.
                if module:
                    imports.append(f"{module}.{alias.name}")
    return imports


_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([.\w]+))", re.MULTILINE
)


def _extract_imports_regex(source_text: str) -> list[str]:
    imports: list[str] = []
    for match in _IMPORT_RE.finditer(source_text):
        name = match.group(1) or match.group(2)
        if name:
            imports.append(name.lstrip("."))
    return imports


def _resolve_internal(imported: str, modules: dict[str, str]) -> str | None:
    """import 대상이 그래프 내부 모듈이면 그 모듈명을, 아니면 None을 돌려준다.

    정확 일치 우선, 없으면 imported의 접두 부분과 일치하는 가장 긴 내부 모듈을 찾는다
    (예: from app.foo.bar import x → app.foo.bar 또는 app.foo).
    """

    if imported in modules:
        return imported
    best: str | None = None
    for candidate in modules:
        if imported == candidate or imported.startswith(candidate + "."):
            if best is None or len(candidate) > len(best):
                best = candidate
        elif candidate.startswith(imported + "."):
            # imported가 패키지이고 내부 모듈이 그 하위인 경우.
            if best is None:
                best = candidate
    return best


def _coerce_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(part) for part in content)
    return str(content)


def _strip_code_fence(text: str) -> str:
    """```mermaid ... ``` 같은 코드펜스를 제거한다(LLM이 붙였을 때 대비)."""

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # 첫 줄(```lang)과 마지막 ``` 제거.
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines)
    return text
