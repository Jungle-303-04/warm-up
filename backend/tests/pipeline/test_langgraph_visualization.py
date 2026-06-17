"""LangGraph proposer 시각화 문서가 코드와 동기화되어 있는지 확인한다."""

from scripts.render_langgraph import DOC_PATH, MERMAID_PATH, build_document, build_mermaid


def test_langgraph_visualization_document_is_current() -> None:
    mermaid = build_mermaid()

    assert MERMAID_PATH.read_text(encoding="utf-8") == mermaid
    assert DOC_PATH.read_text(encoding="utf-8") == build_document(mermaid)
