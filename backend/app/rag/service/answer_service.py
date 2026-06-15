from typing import Any

from sqlalchemy.orm import Session

from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerGraph, RagStore


# 라우터가 LangGraph나 RagAnswerGraph를 직접 알게 만들지 않기 위한 use case 경계
# 라우터 입장에서는 "답변 기능은 answer(db, request)를 가진다"만 알면 됨.
# 추후 그래프 노드 구성, 검색 전략, 프롬프트 조립, 메모리, 에이전트 액션이 추가되어도
# 라우터는 그대로 두고 이 use case 안쪽 조립과 graph 실행 흐름만 바꾸면 된다.
class RagAnswerService:
    """질문 요청의 코드 기준을 SQL에서 확정한 뒤 graph runner에 위임한다."""

    def __init__(self, answer_graph: AnswerGraph, sql_repository: RagStore) -> None:
        self.answer_graph = answer_graph
        self.sql_repository = sql_repository

    def answer(self, db: Session, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """레포/브랜치/커밋 기준의 최신 인덱싱 run을 찾아 답변한다."""

        index_run = self.find_index_run(db, request)
        return self.answer_graph.run(request, index_run)

    def find_index_run(self, db: Session, request: RagAskRequestDTO) -> Any:
        """사용자가 알 수 없는 run_id 대신 레포 기준으로 저장된 코드 스냅샷을 찾는다."""

        index_run = self.sql_repository.find_latest_run(
            db=db,
            repository_full_name=request.repository_full_name,
            branch=request.branch,
            commit_sha=request.commit_sha,
        )

        if index_run is None:
            raise ValueError(
                "indexed repository evidence was not found. "
                "index the repository before asking questions."
            )

        return index_run
