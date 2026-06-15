from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerGraph


class RagAnswerService:
    """RAG 답변 생성 use case를 graph runner에 위임한다."""

    def __init__(
        self,
        answer_graph: AnswerGraph,
    ) -> None:
        self.answer_graph = answer_graph

    def answer(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """질문과 선택 run_id로 관련 청크를 찾고 출처 목록과 함께 답변한다."""

        return self.answer_graph.run(request)
