"""산출물 생성기(결정론/골격) 단위 테스트.

네트워크/실제 LLM 호출 없이 동작한다.
"""

from app.notebooks.domain.artifact_ports import ArtifactContext, GenerationRequest
from app.notebooks.infrastructure.artifact_generators import (
    DeterministicArtifactGenerator,
)


def _ctx(path: str, text: str) -> ArtifactContext:
    return ArtifactContext(
        source_id="s1", source_title="repo", text=text, path=path, language="python"
    )


def test_dependency_builds_import_based_flowchart() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        _ctx("app/main.py", "from app.service import run\nimport os\n"),
        _ctx("app/service.py", "from app.util import helper\n"),
        _ctx("app/util.py", "x = 1\n"),
    ]

    content = gen.generate(
        GenerationRequest(type="dependency", contexts=contexts)
    )

    # Mermaid flowchart 골격
    assert content.startswith("flowchart TD")
    # 내부 모듈 의존 엣지(외부 import os 는 제외)
    assert "app.main" in content
    assert "app.service" in content
    assert "app.util" in content
    assert "-->" in content
    # main -> service, service -> util 두 엣지가 있어야 한다.
    assert content.count("-->") == 2
    # 외부 모듈(os)은 노드/엣지로 등장하지 않는다.
    assert '"os"' not in content


def test_dependency_with_no_python_returns_graph_without_error() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        ArtifactContext(source_id="s", source_title="doc", text="hello", path=None)
    ]

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart TD")
    assert "no python sources" in content


def test_uml_fallback_returns_skeleton_without_error() -> None:
    gen = DeterministicArtifactGenerator()

    content = gen.generate(GenerationRequest(type="uml", contexts=[]))

    assert content.startswith("classDiagram")
    assert "LLM 키가 필요합니다" in content


def test_erd_fallback_returns_skeleton_without_error() -> None:
    gen = DeterministicArtifactGenerator()

    content = gen.generate(GenerationRequest(type="erd", contexts=[]))

    assert content.startswith("erDiagram")
    assert "LLM 키가 필요합니다" in content


def test_change_summary_fallback_returns_markdown() -> None:
    gen = DeterministicArtifactGenerator()

    content = gen.generate(GenerationRequest(type="change_summary", contexts=[]))

    assert content.startswith("## 변경 요약")
    assert "LLM 키가 필요합니다" in content
