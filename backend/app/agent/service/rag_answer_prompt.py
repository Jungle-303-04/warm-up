from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.domain.chat import InferredRepositoryRef
from app.agent.service.repository_context import format_response_ref
from app.rag.api.schema import RagAskResponseDTO

ANSWER_SYSTEM_PROMPT = (
    "You answer in Korean for a code-analysis workspace. "
    "Use only the provided repository evidence. "
    "If the evidence is partial, give the best evidence-based recommendation and clearly mark assumptions. "
    "If code chunks are provided, do not say that code access is needed. "
    "If explicit TODO or unfinished markers are not found in the evidence, say that clearly, "
    "then recommend based on the strongest available code evidence. "
    "If the evidence is truly insufficient, say what is missing instead of inventing details."
)
COMPARISON_SYSTEM_PROMPT = (
    "You answer in Korean for a code-analysis workspace. "
    "The user is asking for functional differences between repository snapshots. "
    "Use the SQL file snapshot summary to understand what changed, and use the provided "
    "code chunks as evidence for what those changes mean. "
    "Do not invent implementation details that are not supported by the evidence. "
    "If the question excludes frontend or UI differences, focus on backend, API, service, "
    "domain, RAG, agent, database, and workflow behavior."
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


def build_comparison_answer_messages(
    question: str,
    snapshot_summary: str,
    chunks_by_run: list[tuple[Any, list[Any]]],
) -> list[Any]:
    """스냅샷 비교 결과와 관련 코드 청크를 LLM 비교 답변 입력으로 만든다."""

    evidence_text = "\n\n".join(
        format_comparison_chunk_for_prompt(run, chunk)
        for run, chunks in chunks_by_run
        for chunk in chunks
    )
    if not evidence_text:
        evidence_text = "(관련 코드 청크 없음)"

    return [
        SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"사용자 질문:\n{question}\n\n"
                f"SQL 파일 스냅샷 비교:\n{snapshot_summary}\n\n"
                f"관련 코드 청크:\n{evidence_text}\n\n"
                "위 정보만 사용해서 기능적 차이를 요약해 주세요. "
                "먼저 결론을 말하고, 그 다음 근거 파일을 짧게 붙여 주세요."
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


def format_comparison_chunk_for_prompt(run: Any, chunk: Any) -> str:
    """SQL chunk 한 개를 브랜치/파일/라인이 보이는 LLM 근거로 포장한다."""

    branch = getattr(run, "branch", None) or "기본 브랜치"
    repository = getattr(run, "repository_full_name", None) or "unknown repository"
    citation = getattr(chunk, "citation", "") or getattr(chunk, "path", "")
    content = (getattr(chunk, "chunk_text", "") or "").strip()
    if len(content) > 1400:
        content = f"{content[:1400]}..."
    return (
        f"[{repository} · {branch}] {citation}\n"
        f"chunk_type={getattr(chunk, 'chunk_type', '')}, "
        f"symbol={getattr(chunk, 'symbol_name', None) or ''}\n"
        f"{content}"
    )


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
