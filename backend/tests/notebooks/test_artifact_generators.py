"""산출물 생성기(결정론/골격) 단위 테스트.

네트워크/실제 LLM 호출 없이 동작한다.
"""

from app.notebooks.domain.artifact_ports import ArtifactContext, GenerationRequest
from app.notebooks.infrastructure.artifact_generators import (
    ChatOpenAIArtifactGenerator,
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

    # Mermaid flowchart 골격(가독성 위해 LR)
    assert content.startswith("flowchart LR")
    # 라벨은 마지막 1~2 세그먼트로 축약되지만, 노드 식별자(n_app_main 등)에
    # 전체 모듈 경로가 남는다.
    assert "n_app_main" in content
    assert "n_app_service" in content
    assert "n_app_util" in content
    assert "-->" in content
    # main -> service, service -> util 두 엣지가 있어야 한다.
    assert content.count("-->") == 2
    # 외부 모듈(os)은 노드/엣지로 등장하지 않는다.
    assert "n_os" not in content


def test_dependency_with_no_python_returns_graph_without_error() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        ArtifactContext(source_id="s", source_title="doc", text="hello", path=None)
    ]

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart LR")
    assert "no python sources" in content


def test_dependency_excludes_isolated_nodes() -> None:
    """import 엣지가 전혀 없는 고립 모듈은 그래프에서 제외된다."""
    gen = DeterministicArtifactGenerator()
    contexts = [
        _ctx("app/main.py", "from app.service import run\n"),
        _ctx("app/service.py", "x = 1\n"),
        # lonely는 아무도 import하지 않고 내부 import도 없는 고립 모듈.
        _ctx("app/lonely.py", "import os\n"),
    ]

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart LR")
    # 연결된 main/service는 남고,
    assert "n_app_main" in content
    assert "n_app_service" in content
    # 고립 노드 lonely는 빠진다.
    assert "n_app_lonely" not in content
    assert content.count("-->") == 1


def test_dependency_groups_packages_into_subgraphs() -> None:
    """서로 다른 상위 패키지 모듈은 subgraph로 그룹화되고 라벨은 축약된다."""
    gen = DeterministicArtifactGenerator()
    contexts = [
        _ctx(
            "app/notebooks/chat.py",
            "from app.repo_rag.client import Embed\n",
        ),
        _ctx("app/repo_rag/client.py", "x = 1\n"),
    ]

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart LR")
    # 상위 패키지(app.notebooks, app.repo_rag)별 subgraph.
    assert "subgraph" in content
    assert '["app.notebooks"]' in content
    assert '["app.repo_rag"]' in content
    # 라벨은 마지막 2세그먼트로 축약(전체경로 아님).
    assert '["notebooks.chat"]' in content
    assert '["repo_rag.client"]' in content
    # 패키지 간 의존 엣지.
    assert content.count("-->") == 1


def test_dependency_collapses_to_packages_when_over_node_cap() -> None:
    """노드 수가 상한을 넘으면 상위 패키지 단위로 묶어 축소한다."""
    from app.notebooks.infrastructure.artifact_generators import (
        MAX_DEPENDENCY_NODES,
    )

    gen = DeterministicArtifactGenerator()
    # 두 패키지(pkg_a, pkg_b)에 상한을 넘는 수의 모듈을 만들고, 각 a_i가 b_i를 import.
    half = MAX_DEPENDENCY_NODES  # 두 패키지 합쳐 2*half > 상한
    contexts = []
    for i in range(half):
        contexts.append(
            _ctx(f"app/pkg_a/mod{i}.py", f"from app.pkg_b.mod{i} import thing\n")
        )
        contexts.append(_ctx(f"app/pkg_b/mod{i}.py", "thing = 1\n"))

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart LR")
    # 축소 후에는 패키지 노드(app.pkg_a → app.pkg_b) 한 쌍만 남는다.
    assert "n_app_pkg_a" in content
    assert "n_app_pkg_b" in content
    # 개별 모듈 노드는 사라진다.
    assert "n_app_pkg_a_mod0" not in content
    # 그룹 간 엣지는 단 하나로 축약된다.
    assert content.count("-->") == 1


def test_dependency_no_internal_edges_returns_notice() -> None:
    """파이썬 소스는 있으나 서로 import하지 않으면 안내 그래프를 돌려준다(에러 아님)."""
    gen = DeterministicArtifactGenerator()
    contexts = [
        _ctx("app/a.py", "import os\n"),
        _ctx("app/b.py", "import sys\n"),
    ]

    content = gen.generate(GenerationRequest(type="dependency", contexts=contexts))

    assert content.startswith("flowchart LR")
    assert "no internal dependencies" in content


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
    assert "요약할 컨텍스트를 찾지 못했습니다" in content


def test_change_summary_from_code_without_key() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        _ctx(
            "app/api/router.py",
            (
                "from fastapi import APIRouter\n"
                "router = APIRouter()\n"
                "@router.get('/users')\n"
                "def list_users():\n"
                "    return []\n"
                "class UserService:\n"
                "    def find(self): ...\n"
            ),
        ),
        ArtifactContext(
            source_id="s1",
            source_title="repo",
            text="# 문서\n\n완전히 다른 운영 문서입니다.",
            path="docs/ops.md",
            language="markdown",
        ),
    ]

    content = gen.generate(
        GenerationRequest(type="change_summary", contexts=contexts)
    )

    assert content.startswith("## 변경 요약")
    assert "LLM 키가 필요합니다" not in content
    assert "`app/api/router.py`" in content
    assert "UserService" in content
    assert "list_users" in content
    assert "docs/ops.md" not in content


# ── 하이브리드(AST 골격): 키 없이도 Python 클래스/ORM이면 실제 다이어그램 ──


def test_uml_from_python_classes_without_key() -> None:
    """파이썬 클래스가 있으면 키 없이도 레이어드 UML flowchart를 만든다."""
    gen = DeterministicArtifactGenerator()
    src = "class Base: ...\nclass App(Base):\n    state: int\n    def start(self): ...\n"

    content = gen.generate(
        GenerationRequest(type="uml", contexts=[_ctx("app/application/app.py", src)])
    )

    assert content.startswith("flowchart TB")
    assert "LLM 키가 필요합니다" not in content
    assert 'subgraph layer_application["Application / Service"]' in content
    assert "c_App" in content
    assert "actions: start()" in content
    assert "state: state" in content
    assert "c_App -->|extends| c_Base" in content  # 내부 클래스 상속 관계


def test_erd_from_orm_models_without_key() -> None:
    """ORM 모델(__tablename__/Column/ForeignKey)이면 키 없이도 실제 erDiagram을 만든다."""
    gen = DeterministicArtifactGenerator()
    src = (
        'class User(Base):\n    __tablename__ = "users"\n    id = Column(Integer)\n'
        'class Post(Base):\n    __tablename__ = "posts"\n'
        '    id = Column(Integer)\n    user_id = Column(Integer, ForeignKey("users.id"))\n'
    )

    content = gen.generate(GenerationRequest(type="erd", contexts=[_ctx("app/models.py", src)]))

    assert content.startswith("erDiagram")
    assert "LLM 키가 필요합니다" not in content
    assert "users" in content and "posts" in content
    assert "}o--||" in content  # FK 관계


def test_erd_extracts_sqlalchemy_relationships_without_foreign_key() -> None:
    gen = DeterministicArtifactGenerator()
    src = (
        "class User(Base):\n"
        '    __tablename__ = "users"\n'
        "    id = Column(Integer)\n"
        '    posts = relationship("Post", back_populates="user")\n'
        "class Post(Base):\n"
        '    __tablename__ = "posts"\n'
        "    id = Column(Integer)\n"
        '    user = relationship("User", back_populates="posts")\n'
    )

    content = gen.generate(GenerationRequest(type="erd", contexts=[_ctx("app/models.py", src)]))

    assert content.startswith("erDiagram")
    assert "users" in content
    assert "posts" in content
    assert "users }o--|| posts : relationship" in content
    assert "posts }o--|| users : relationship" in content


def test_erd_sanitizes_sqlalchemy_vector_columns() -> None:
    """SQLAlchemy 타입 힌트가 Mermaid ERD의 비문법 타입으로 새지 않아야 한다."""
    gen = DeterministicArtifactGenerator()
    src = (
        "class NotebookChunkModel(Base):\n"
        '    __tablename__ = "notebook_chunks"\n'
        "    id: Mapped[str] = mapped_column(String, primary_key=True)\n"
        "    source_id: Mapped[str] = mapped_column(ForeignKey('notebook_sources.id'))\n"
        "    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))\n"
    )

    content = gen.generate(GenerationRequest(type="erd", contexts=[_ctx("app/models.py", src)]))

    assert content.startswith("erDiagram")
    assert "list<" not in content
    assert "embedding" in content
    assert "notebook_chunks" in content


def test_chat_openai_generator_prefers_deterministic_erd() -> None:
    """LLM이 깨진 Mermaid를 반환해도 ERD는 정적 생성 결과를 사용한다."""

    class BadModel:
        def invoke(self, _prompt: str) -> str:
            return "erDiagram\n    bad {\n        list<float> embedding\n    }\n"

    gen = ChatOpenAIArtifactGenerator(BadModel())
    src = (
        "class User(Base):\n"
        '    __tablename__ = "users"\n'
        "    id = Column(Integer)\n"
    )

    content = gen.generate(GenerationRequest(type="erd", contexts=[_ctx("app/models.py", src)]))

    assert "list<float>" not in content
    assert "users" in content


def test_uml_from_typescript_interfaces_without_key() -> None:
    gen = DeterministicArtifactGenerator()
    ctx = ArtifactContext(
        source_id="s1",
        source_title="repo",
        path="apps/web/src/lib/types.ts",
        language="typescript",
        text=(
            "export interface Source {\n"
            "  id: string;\n"
            "  title: string;\n"
            "}\n"
            "export class SourceStore {\n"
            "  sources: Source[] = [];\n"
            "  add(source: Source) {}\n"
            "}\n"
        ),
    )

    content = gen.generate(GenerationRequest(type="uml", contexts=[ctx]))

    assert content.startswith("flowchart TB")
    assert 'subgraph layer_domain["Domain / Contract"]' in content
    assert "c_Source" in content
    assert "state: id, title" in content
    assert "c_SourceStore" in content
    assert "actions: add()" in content
    assert "c_SourceStore -->|uses| c_Source" in content


def test_uml_without_extractable_symbols_falls_back_to_skeleton() -> None:
    """추출할 클래스가 없으면 안내 골격으로 폴백한다."""
    gen = DeterministicArtifactGenerator()

    content = gen.generate(GenerationRequest(type="uml", contexts=[_ctx("a.py", "x = 1\n")]))

    assert content.startswith("classDiagram")
    assert "LLM 키가 필요합니다" in content


def test_change_summary_prefers_recent_commits() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        ArtifactContext(
            source_id="s1",
            source_title="repo",
            path="__recent_commits__.md",
            language="markdown",
            text="# 최근 커밋\n- `abc123` 2026-06-18 woonyong: 색인 완료 표시 개선\n",
        ),
        _ctx(
            "app/api/router.py",
            "class ApiRouter:\n    def generate(self): ...\n",
        ),
    ]

    content = gen.generate(GenerationRequest(type="change_summary", contexts=contexts))

    assert "### 최근 커밋 기준" in content
    assert "색인 완료 표시 개선" in content
    assert "### 코드 기준 핵심" in content


def test_change_summary_includes_changed_file_links_from_recent_commits() -> None:
    gen = DeterministicArtifactGenerator()
    contexts = [
        ArtifactContext(
            source_id="s1",
            source_title="repo",
            path="__recent_commits__.md",
            language="markdown",
            source_url="https://github.com/org/repo",
            branch="main",
            text=(
                "# 최근 커밋\n"
                "- [`abc123`](https://github.com/org/repo/commit/abc123) "
                "2026-06-18 woonyong: 색인 완료 표시 개선\n"
                "  - modified [`app/api/router.py`]"
                "(https://github.com/org/repo/blob/main/app/api/router.py)\n"
            ),
        ),
        ArtifactContext(
            source_id="s1",
            source_title="repo",
            path="app/api/router.py",
            language="python",
            source_url="https://github.com/org/repo",
            branch="main",
            text="class ApiRouter:\n    def generate(self): ...\n",
        ),
    ]

    content = gen.generate(GenerationRequest(type="change_summary", contexts=contexts))

    assert "### 변경 파일 링크" in content
    assert "`modified` [`app/api/router.py`](https://github.com/org/repo/blob/main/app/api/router.py)" in content
    assert "[`app/api/router.py`](https://github.com/org/repo/blob/main/app/api/router.py)" in content
