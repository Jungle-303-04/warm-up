from typing import TypedDict

from langgraph.graph import END, StateGraph

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


class RagAnswerState(TypedDict, total=False):
    request: RagAskRequestDTO
    rows: list[VectorResultRow]
    answer: str
    sources: list[RagAskSourceDTO]
    response: RagAskResponseDTO


class RagAnswerGraph:
    """LangGraph로 RAG 답변 생성 흐름을 명시적으로 연결한다."""

    def __init__(
        self,
        vector_repository: VectorStore,
        llm_client: LlmClient,
    ) -> None:
        self.vector_repository = vector_repository
        self.llm_client = llm_client
        self.graph = self.build_graph()

    def run(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """질문 요청을 graph state로 실행하고 최종 응답 DTO를 반환한다."""

        state = self.graph.invoke({"request": request})
        return state["response"]

    def build_graph(self):
        graph = StateGraph(RagAnswerState)
        graph.add_node("retrieve_vector", self.retrieve_vector)
        graph.add_node("generate_answer", self.generate_answer)
        graph.add_node("build_response", self.build_response)

        graph.set_entry_point("retrieve_vector")
        graph.add_edge("retrieve_vector", "generate_answer")
        graph.add_edge("generate_answer", "build_response")
        graph.add_edge("build_response", END)

        return graph.compile()

    def retrieve_vector(self, state: RagAnswerState) -> RagAnswerState:
        """질문과 run_id로 vector DB에서 관련 청크를 찾는다."""

        request = state["request"]
        search_result = self.vector_repository.search(
            query=request.question,
            limit=request.limit,
            run_id=request.run_id,
        )
        return {"rows": parse_vector_result(search_result)}

    def generate_answer(self, state: RagAnswerState) -> RagAnswerState:
        """검색된 근거가 있으면 LLM 답변을 만들고, 없으면 기본 답변을 사용한다."""

        request = state["request"]
        rows = state.get("rows", [])

        if not rows:
            return {
                "answer": NO_EVIDENCE_ANSWER,
                "sources": [],
            }

        return {
            "answer": self.llm_client.answer_with_evidence(
                question=request.question,
                documents=[row.document for row in rows],
                metadatas=[row.metadata for row in rows],
            ),
            "sources": build_sources(rows),
        }

    def build_response(self, state: RagAnswerState) -> RagAnswerState:
        """Graph state를 API 응답 DTO로 포장한다."""

        request = state["request"]
        return {
            "response": RagAskResponseDTO(
                answer=state["answer"],
                run_id=request.run_id,
                sources=state.get("sources", []),
            )
        }


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
