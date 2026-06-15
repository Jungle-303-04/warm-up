from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerGraph


# 라우터가 LangGraph나 RagAnswerGraph를 직접 알게 만들지 않기 위한 use case 경계
# 라우터 입장에서는 "답변 기능은 answer(request)를 가진다"만 알면 됨.
# 추후 그래프 노드 구성, 검색 전략, 프롬프트 조립, 메모리, 에이전트 액션이 추가되어도
# 라우터는 그대로 두고 이 use case 안쪽 조립과 graph 실행 흐름만 바꾸면 된다.
class RagAnswerService:
    """RAG 답변 생성 use case를 graph runner에 위임한다."""

    def __init__(self, answer_graph: AnswerGraph) -> None:
        self.answer_graph = answer_graph

    def answer(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """질문과 선택 run_id로 관련 청크를 찾고 출처 목록과 함께 답변한다."""

        return self.answer_graph.run(request)
