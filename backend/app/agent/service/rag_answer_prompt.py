from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.domain.chat import InferredRepositoryRef
from app.agent.service.repository_context import format_response_ref
from app.rag.api.schema import RagAskResponseDTO

ANSWER_SYSTEM_PROMPT = (
    "You answer in Korean for a code-analysis workspace. "
    "Use only the provided repository evidence. "
    "If the evidence is insufficient, say what is missing instead of inventing details."
)


def build_answer_messages(
    question: str,
    rag_response: RagAskResponseDTO,
) -> list[Any]:
    """RAG 검색 결과를 LLM이 최종 답변으로 바꿀 수 있는 최소 메시지로 만든다."""

    evidence_text = "\n\n".join(
        format_source_for_prompt(index, source)
        for index, source in enumerate(rag_response.sources[:5], start=1)
    )
    basis_text = "\n".join(
        format_response_ref(ref)
        for ref in rag_response.repository_refs
        if ref.repository_full_name
    )
    return [
        SystemMessage(content=ANSWER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"질문:\n{question}\n\n"
                f"답변 기준:\n{basis_text}\n\n"
                f"검색 근거:\n{evidence_text}\n\n"
                "위 근거만 사용해서 답변해 주세요."
            )
        ),
    ]


def build_no_evidence_answer(refs: list[InferredRepositoryRef]) -> str:
    """선택된 기준 안에서 vector 근거가 없을 때 확정적으로 답한다."""

    basis = ", ".join(format_response_ref(ref) for ref in refs) or "선택된 분석 결과"
    return f"{basis} 안에서 관련 RAG 근거를 찾지 못했습니다. 질문을 더 구체적으로 적거나 레포지토리를 다시 분석해 주세요."


def build_evidence_fallback_answer(response: RagAskResponseDTO) -> str:
    """LLM 호출이 실패했을 때도 찾은 출처 목록은 사용자에게 보여준다."""

    lines = ["관련 근거를 찾았습니다. LLM 답변 생성에 실패해 출처 중심으로 요약합니다."]
    for index, source in enumerate(response.sources[:5], start=1):
        lines.append(f"{index}. {source.citation or source.path or '출처 정보 없음'}")
    return "\n".join(lines)


def format_source_for_prompt(index: int, source: Any) -> str:
    citation = source.citation or source.path or "출처 정보 없음"
    content = (source.content or "").strip()
    if len(content) > 1600:
        content = f"{content[:1600]}..."
    return f"[{index}] {citation}\n{content}"


def get_message_content(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or item.get("content") or item)
            if isinstance(item, dict)
            else str(item)
            for item in content
        ).strip()
    return str(content).strip()
