from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagAskRunReferenceDTO,
    RagAskSourceDTO,
)
from app.rag.domain.vector_result import VectorResultRow, parse_vector_result
from app.rag.service.ports import VectorStore


NO_EVIDENCE_ANSWER = (
    "저장된 RAG 근거를 찾지 못했습니다. 먼저 레포지토리 분석을 실행해 주세요."
)


class RagAnswerState(TypedDict, total=False):
    # LangGraph의 state는 노드들이 이어서 읽고 쓰는 공유 작업 메모리다.
    # 각 노드는 전체 state를 다시 만들지 않고, 자신이 추가/수정한 값만 dict로 반환한다.
    request: RagAskRequestDTO
    index_run: Any
    rows: list[VectorResultRow]
    sources: list[RagAskSourceDTO]
    response: RagAskResponseDTO


class RagAnswerGraph:
    """LangGraph로 RAG 근거 검색 흐름을 명시적으로 연결한다."""

    def __init__(
        self,
        vector_repository: VectorStore,
    ) -> None:
        self.vector_repository = vector_repository
        self.graph = self.build_graph()

    def run(self, request: RagAskRequestDTO, index_run: Any) -> RagAskResponseDTO:
        """질문 요청을 graph state로 실행하고 최종 응답 DTO를 반환한다."""

        # index_run은 graph가 직접 찾지 않는다.
        # RagAnswerService가 SQL에서 레포/브랜치/커밋 기준을 먼저 확정하고,
        # graph는 그 확정된 코드 스냅샷 안에서만 벡터 검색을 수행한다.
        state = self.graph.invoke({"request": request, "index_run": index_run})
        return state["response"]

    def build_graph(self):
        graph = StateGraph(RagAnswerState)

        # RAG는 agent가 사용할 검색 tool이다.
        # 최종 자연어 답변 생성은 agent LLM이 맡고, 여기서는 evidence만 찾는다.
        graph.add_node("retrieve_vector", self.retrieve_vector)
        graph.add_node("build_response", self.build_response)

        graph.set_entry_point("retrieve_vector")
        graph.add_edge("retrieve_vector", "build_response")
        graph.add_edge("build_response", END)

        return graph.compile()

    def retrieve_vector(self, state: RagAnswerState) -> RagAnswerState:
        """질문과 확정된 commit 기준으로 vector DB에서 관련 청크를 찾는다."""

        request = state["request"]
        index_runs = normalize_index_runs(state["index_run"])

        # 사용자가 임의로 적은 보드/질문 내용은 신뢰 기준이 아니다.
        # SQL에서 확정한 index_run의 repository_full_name, branch, commit_sha를 필터로 써서
        # 실제 저장된 코드 스냅샷 안의 chunk만 검색 후보로 둔다.
        rows: list[VectorResultRow] = []
        for index_run in index_runs:
            search_result = self.vector_repository.search(
                query=request.question,
                limit=request.limit,
                repository_full_name=index_run.repository_full_name,
                branch=index_run.branch,
                commit_sha=index_run.commit_sha,
            )
            rows.extend(parse_vector_result(search_result))

        # Chroma 결과는 ids/documents/metadatas/distances가 따로 오므로,
        # 다음 노드가 다루기 쉬운 row 목록으로 변환해서 state에 rows로 추가한다.
        return {"rows": sort_rows_by_distance(rows)}

    def build_response(self, state: RagAnswerState) -> RagAnswerState:
        """Graph state를 API 응답 DTO로 포장한다."""

        index_runs = normalize_index_runs(state["index_run"])
        primary_run = index_runs[0]
        rows = state.get("rows", [])
        # run_id는 사용자가 질문할 때 고르는 기준이 아니라 추적용 번호다.
        # 응답에는 실제 답변 기준이 된 repository_full_name, branch, commit_sha를 함께 내려준다.
        return {
            "response": RagAskResponseDTO(
                answer=build_retrieval_summary(rows),
                repository_full_name=primary_run.repository_full_name,
                branch=primary_run.branch,
                commit_sha=primary_run.commit_sha,
                run_id=primary_run.id,
                repository_refs=[
                    RagAskRunReferenceDTO(
                        run_id=index_run.id,
                        repository_full_name=index_run.repository_full_name,
                        branch=index_run.branch,
                        commit_sha=index_run.commit_sha,
                    )
                    for index_run in index_runs
                ],
                sources=build_sources(rows),
            )
        }


def build_sources(rows: list[VectorResultRow]) -> list[RagAskSourceDTO]:
    """agent가 최종 답변에 사용할 citation, path, 거리, 원문을 검색 결과에서 추출한다."""

    sources: list[RagAskSourceDTO] = []
    for row in rows:
        # vector metadata에 저장해 둔 citation/path/chunk_type을 API 응답용 출처 DTO로 옮긴다.
        # 이 값들이 있어야 사용자가 LLM 답변이 어떤 코드 조각에서 나온 것인지 확인할 수 있다.
        sources.append(
            RagAskSourceDTO(
                citation=str(row.metadata.get("citation", "")),
                path=str(row.metadata.get("path", "")),
                chunk_type=str(row.metadata.get("chunk_type", "")),
                distance=row.distance,
                content=row.document,
            )
        )
    return sources


def build_retrieval_summary(rows: list[VectorResultRow]) -> str:
    """API answer 필드에는 LLM 답변이 아니라 검색 결과 요약을 담는다."""

    if not rows:
        return NO_EVIDENCE_ANSWER
    return f"RAG 검색 결과 {len(rows)}개를 찾았습니다. 최종 답변은 agent가 이 근거를 바탕으로 생성합니다."


def normalize_index_runs(index_run: Any) -> list[Any]:
    """단일 run과 run 목록을 graph 내부 공통 형태로 맞춘다."""

    if isinstance(index_run, list):
        return index_run

    return [index_run]


def sort_rows_by_distance(rows: list[VectorResultRow]) -> list[VectorResultRow]:
    """여러 레포 검색 결과를 LLM에 넘기기 전에 가까운 근거 순서로 정렬한다."""

    return sorted(
        rows,
        key=lambda row: row.distance if row.distance is not None else float("inf"),
    )
