from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagAskSourceDTO,
)
from app.rag.domain.vector_result import VectorResultRow, parse_vector_result
from app.rag.service.ports import LlmClient, VectorStore


NO_EVIDENCE_ANSWER = (
    "저장된 RAG 근거를 찾지 못했습니다. 먼저 레포지토리 분석을 실행해 주세요."
)


class RagAnswerService:
    """벡터 검색으로 근거를 찾고, 그 근거만 LLM에 넘겨 답변을 만든다."""

    def __init__(
        self,
        vector_repository: VectorStore,
        llm_client: LlmClient,
    ) -> None:
        self.vector_repository = vector_repository
        self.llm_client = llm_client

    def answer(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """질문과 선택 run_id로 관련 청크를 찾고 출처 목록과 함께 답변한다."""

        search_result = self.vector_repository.search(
            query=request.question,
            limit=request.limit,
            run_id=request.run_id,
        )
        rows = parse_vector_result(search_result)

        if not rows:
            return RagAskResponseDTO(
                answer=NO_EVIDENCE_ANSWER,
                run_id=request.run_id,
                sources=[],
            )

        return RagAskResponseDTO(
            answer=self.llm_client.answer_with_evidence(
                question=request.question,
                documents=[row.document for row in rows],
                metadatas=[row.metadata for row in rows],
            ),
            run_id=request.run_id,
            sources=build_sources(rows),
        )


def build_sources(rows: list[VectorResultRow]) -> list[RagAskSourceDTO]:
    """LLM 답변 아래에 노출할 citation, path, 거리 정보를 검색 결과에서 추출한다."""

    sources: list[RagAskSourceDTO] = []
    for row in rows:
        sources.append(
            RagAskSourceDTO(
                citation=str(row.metadata.get("citation", "")),
                path=str(row.metadata.get("path", "")),
                chunk_type=str(row.metadata.get("chunk_type", "")),
                distance=row.distance,
            )
        )
    return sources
