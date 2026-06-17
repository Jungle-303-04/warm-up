"""LangGraph proposer 그래프 문서/다이어그램 갱신 도구.

기본 실행은 Mermaid 문서와 .mmd 파일을 갱신한다. --check는 현재 문서가 코드의
그래프와 일치하는지 확인하고, --png는 네트워크가 가능할 때 Mermaid.ink 기반 PNG도
생성한다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.pipeline.proposer import LangGraphProposer

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs" / "woonyong" / "langgraph-proposer-graph.md"
MERMAID_PATH = ROOT / "docs" / "woonyong" / "assets" / "langgraph-proposer.mmd"
PNG_PATH = ROOT / "docs" / "woonyong" / "assets" / "langgraph-proposer.png"


def build_mermaid() -> str:
    proposer = LangGraphProposer(
        chat_model=FakeListChatModel(responses=['{"proposals": []}'])
    )
    return proposer._graph.get_graph().draw_mermaid().strip() + "\n"


def build_document(mermaid: str) -> str:
    return f"""# LangGraph 제안 그래프

이 문서는 `backend/app/pipeline/proposer.py`의 `LangGraphProposer` 실행 흐름을
시각화한 자료입니다. 그래프 노드나 조건부 엣지를 수정한 뒤에는 아래 명령으로 문서를
다시 생성하세요.

```bash
cd backend
uv run python scripts/render_langgraph.py
```

PNG까지 갱신하려면 네트워크가 가능한 환경에서 다음 명령을 사용합니다.

```bash
cd backend
uv run python scripts/render_langgraph.py --png
```

문서가 최신인지 확인하는 검증 명령입니다.

```bash
cd backend
uv run python scripts/render_langgraph.py --check
```

## 현재 그래프

```mermaid
{mermaid}```

## 노드 역할

- `gather_evidence`: 검색 청크와 코드 참조를 LLM 입력 메시지와 evidence map으로 정리합니다.
- `agent`: LLM이 근거를 분석하고, 사용 가능한 MCP 도구가 있으면 도구 호출 여부를 결정합니다.
- `execute_tools`: LLM의 tool call을 MCP client로 실행하고 결과를 메시지에 추가합니다.
- `draft`: 마지막 AI 응답 또는 최종 LLM 호출 결과를 `ProposalDraft` 목록으로 파싱합니다.

## 갱신 정책

- LangGraph 노드, 엣지, 조건부 라우팅, 상태 필드를 바꾸면 이 문서를 함께 갱신합니다.
- `backend/tests/pipeline/test_langgraph_visualization.py`가 코드 그래프와 문서의 Mermaid 블록
  일치 여부를 검사합니다.
- PNG는 리뷰/공유용 산출물이며, 자동 검증의 기준은 Mermaid 텍스트입니다.
"""


def write_outputs(mermaid: str, *, write_png: bool) -> None:
    MERMAID_PATH.parent.mkdir(parents=True, exist_ok=True)
    MERMAID_PATH.write_text(mermaid, encoding="utf-8")
    DOC_PATH.write_text(build_document(mermaid), encoding="utf-8")
    if write_png:
        proposer = LangGraphProposer(
            chat_model=FakeListChatModel(responses=['{"proposals": []}'])
        )
        png_bytes = proposer._graph.get_graph().draw_mermaid_png()
        PNG_PATH.write_bytes(png_bytes)


def check_outputs(mermaid: str) -> bool:
    expected_doc = build_document(mermaid)
    return (
        DOC_PATH.exists()
        and MERMAID_PATH.exists()
        and DOC_PATH.read_text(encoding="utf-8") == expected_doc
        and MERMAID_PATH.read_text(encoding="utf-8") == mermaid
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="문서 최신 여부만 확인")
    parser.add_argument("--png", action="store_true", help="PNG 파일도 생성")
    args = parser.parse_args()

    mermaid = build_mermaid()
    if args.check:
        if check_outputs(mermaid):
            print("LangGraph 문서가 최신입니다.")
            return 0
        print("LangGraph 문서가 최신 코드와 다릅니다. render_langgraph.py를 실행하세요.")
        return 1

    write_outputs(mermaid, write_png=args.png)
    print(f"wrote {DOC_PATH}")
    print(f"wrote {MERMAID_PATH}")
    if args.png:
        print(f"wrote {PNG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
