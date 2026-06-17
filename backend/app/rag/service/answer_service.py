from typing import Any

from sqlalchemy.orm import Session

from app.rag.api.schema import (
    RagAskRepositoryRefDTO,
    RagAskRequestDTO,
    RagAskResponseDTO,
)
from app.rag.service.ports import AnswerGraph, RagStore


class RagAnswerService:
    """라우터 요청을 실제 인덱싱 run으로 확정하고 RAG 검색 graph를 실행한다."""

    def __init__(self, answer_graph: AnswerGraph, sql_repository: RagStore) -> None:
        self.answer_graph = answer_graph
        self.sql_repository = sql_repository

    def answer(self, db: Session, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """레포/브랜치/커밋 기준의 최신 인덱싱 run들을 찾아 근거를 검색한다."""

        index_runs = self.find_index_runs(db, request)
        return self.answer_graph.run(request, index_runs)

    def find_index_run(self, db: Session, request: RagAskRequestDTO) -> Any:
        """사용자가 알 수 없는 run_id 대신 레포 기준으로 저장된 코드 스냅샷을 찾는다."""

        return self.find_index_run_by_ref(
            db=db,
            ref=self.build_single_repository_ref(request),
        )

    def find_index_runs(self, db: Session, request: RagAskRequestDTO) -> list[Any]:
        """요청에 포함된 하나 이상의 레포 기준을 실제 저장된 run 목록으로 확정한다."""

        return [
            self.find_index_run_by_ref(db=db, ref=repository_ref)
            for repository_ref in self.build_repository_refs(request)
        ]

    def find_index_run_by_ref(
        self,
        db: Session,
        ref: RagAskRepositoryRefDTO,
    ) -> Any:
        """레포/브랜치/커밋 기준 하나를 가장 최근 저장 run으로 해석한다."""

        index_run = self.sql_repository.find_latest_run(
            db=db,
            repository_full_name=ref.repository_full_name,
            branch=ref.branch,
            commit_sha=ref.commit_sha,
        )

        if index_run is None:
            raise ValueError(
                f"indexed repository evidence was not found for {ref.repository_full_name}. "
                "index the repository before asking questions."
            )

        return index_run

    def build_repository_refs(
        self,
        request: RagAskRequestDTO,
    ) -> list[RagAskRepositoryRefDTO]:
        """다중 DTO가 있으면 그대로 쓰고, 없으면 기존 단일 필드를 다중 형태로 감싼다."""

        if request.repository_refs:
            return request.repository_refs

        return [self.build_single_repository_ref(request)]

    def build_single_repository_ref(
        self,
        request: RagAskRequestDTO,
    ) -> RagAskRepositoryRefDTO:
        """단일 레포 필드를 내부 공통 ref 구조로 바꾼다."""

        if request.repository_full_name is None:
            raise ValueError("repository_full_name or repository_refs must be provided")

        return RagAskRepositoryRefDTO(
            repository_full_name=request.repository_full_name,
            branch=request.branch,
            commit_sha=request.commit_sha,
        )
