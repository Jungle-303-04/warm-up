import os

from openai import OpenAI

from app.domains.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagAskSourceDTO,
)
from app.domains.rag.infrastructure.vector_repository import RagVectorRepository


DEFAULT_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = (
    "You answer in Korean. Use only the provided repository evidence. "
    "If the evidence is insufficient, say what is missing. "
    "Keep the answer practical and include source citations naturally."
)
NO_EVIDENCE_ANSWER = "저장된 RAG 근거를 찾지 못했습니다. 먼저 레포지토리 분석을 실행해 주세요."


class RagAnswerService:
    def __init__(
        self,
        vector_repository: RagVectorRepository,
        model: str = DEFAULT_LLM_MODEL,
    ) -> None:
        self.vector_repository = vector_repository
        self.model = model
        self.client = OpenAI()

    def answer(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        search_result = self.vector_repository.search(
            query=request.question,
            limit=request.limit,
            run_id=request.run_id,
        )
        documents = search_result.get("documents", [[]])[0] or []
        metadatas = search_result.get("metadatas", [[]])[0] or []
        distances = search_result.get("distances", [[]])[0] or []

        if not documents:
            return RagAskResponseDTO(
                answer=NO_EVIDENCE_ANSWER,
                run_id=request.run_id,
                sources=[],
            )

        answer = self.create_llm_answer(
            question=request.question,
            documents=documents,
            metadatas=metadatas,
        )
        return RagAskResponseDTO(
            answer=answer,
            run_id=request.run_id,
            sources=build_sources(metadatas, distances),
        )

    def create_llm_answer(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": build_user_prompt(question, documents, metadatas),
                },
            ],
        )
        return response.output_text.strip()


def build_user_prompt(
    question: str,
    documents: list[str],
    metadatas: list[dict],
) -> str:
    evidence_blocks = []
    for index, document in enumerate(documents, start=1):
        metadata = get_list_value(metadatas, index - 1, {}) or {}
        citation = metadata.get("citation", "unknown")
        evidence_blocks.append(
            f"[{index}] citation={citation}\n{document.strip()}"
        )

    return (
        f"질문:\n{question.strip()}\n\n"
        "근거:\n"
        + "\n\n".join(evidence_blocks)
    )


def build_sources(
    metadatas: list[dict],
    distances: list[float],
) -> list[RagAskSourceDTO]:
    sources: list[RagAskSourceDTO] = []
    for index, metadata in enumerate(metadatas):
        sources.append(
            RagAskSourceDTO(
                citation=str(metadata.get("citation", "")),
                path=str(metadata.get("path", "")),
                chunk_type=str(metadata.get("chunk_type", "")),
                distance=get_list_value(distances, index, None),
            )
        )
    return sources


def get_list_value(values: list, index: int, default):
    if index >= len(values):
        return default
    return values[index]
