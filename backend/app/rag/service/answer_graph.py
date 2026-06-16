from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.rag.api.schema import (
    RagAskRequestDTO,
    RagAskResponseDTO,
    RagAskRunReferenceDTO,
    RagAskSourceDTO,
)
from app.rag.domain.vector_result import VectorResultRow, parse_vector_result
from app.rag.service.ports import LlmClient, VectorStore


EvidenceRoute = Literal["has_evidence", "no_evidence"]
HAS_EVIDENCE_ROUTE: EvidenceRoute = "has_evidence"
NO_EVIDENCE_ROUTE: EvidenceRoute = "no_evidence"

NO_EVIDENCE_ANSWER = (
    "저장된 RAG 근거를 찾지 못했습니다. 먼저 레포지토리 분석을 실행해 주세요."
)


class RagAnswerState(TypedDict, total=False):
    # LangGraph의 state는 노드들이 이어서 읽고 쓰는 공유 작업 메모리다.
    # 각 노드는 전체 state를 다시 만들지 않고, 자신이 추가/수정한 값만 dict로 반환한다.
    request: RagAskRequestDTO
    index_run: Any
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

    def run(self, request: RagAskRequestDTO, index_run: Any) -> RagAskResponseDTO:
        """질문 요청을 graph state로 실행하고 최종 응답 DTO를 반환한다."""

        # index_run은 graph가 직접 찾지 않는다.
        # RagAnswerService가 SQL에서 레포/브랜치/커밋 기준을 먼저 확정하고,
        # graph는 그 확정된 코드 스냅샷 안에서만 검색과 답변 생성을 수행한다.
        state = self.graph.invoke({"request": request, "index_run": index_run})
        return state["response"]

    def build_graph(self):
        graph = StateGraph(RagAnswerState)

        # 현재 graph는 완성형 agent workflow가 아니라 RAG 답변용 최소 흐름이다.
        # 근거 검색 이후에는 "근거 있음 / 근거 없음"을 조건부 엣지로 분기한다.
        graph.add_node("retrieve_vector", self.retrieve_vector)
        graph.add_node("generate_answer", self.generate_answer)
        graph.add_node("build_no_evidence_answer", self.build_no_evidence_answer)
        graph.add_node("build_response", self.build_response)

        # retrieve_vector 이후에는 rows 존재 여부로 다음 노드를 고른다.
        # rows가 있으면 LLM 답변 생성으로 가고, 없으면 재검색/확장 지점이 될 no-evidence 노드로 간다.
        graph.set_entry_point("retrieve_vector")
        graph.add_conditional_edges(
            "retrieve_vector",
            self.route_after_retrieval,
            {
                HAS_EVIDENCE_ROUTE: "generate_answer",
                NO_EVIDENCE_ROUTE: "build_no_evidence_answer",
            },
        )
        graph.add_edge("generate_answer", "build_response")
        graph.add_edge("build_no_evidence_answer", "build_response")
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

    def route_after_retrieval(self, state: RagAnswerState) -> EvidenceRoute:
        """검색 근거 존재 여부에 따라 LLM 호출 여부를 graph edge에서 결정한다."""

        if state.get("rows"):
            return HAS_EVIDENCE_ROUTE
        return NO_EVIDENCE_ROUTE

    def generate_answer(self, state: RagAnswerState) -> RagAnswerState:
        """검색된 근거가 있을 때 LLM 답변을 만든다."""

        request = state["request"]
        rows = state.get("rows", [])

        # 현재 LLM 연결은 RAG 답변 텍스트 생성까지만 담당한다.
        # 에이전트 액션 선택, 보드 수정 제안 실행, GitHub issue 생성 같은 workflow는
        # 아직 이 graph의 노드/엣지로 들어와 있지 않다.
        return {
            "answer": self.llm_client.answer_with_evidence(
                question=request.question,
                documents=[row.document for row in rows],
                metadatas=[row.metadata for row in rows],
            ),
            "sources": build_sources(rows),
        }

    def build_no_evidence_answer(self, state: RagAnswerState) -> RagAnswerState:
        """검색 근거가 없을 때 LLM 추측을 막고 기본 답변을 만든다."""

        # 지금은 기본 답변만 만들지만, 이후에는 이 노드를 SQL 검색, 질문 재작성,
        # 검색 범위 확장, 사용자 재질문 같은 재검색 workflow로 교체할 수 있다.
        return {
            "answer": NO_EVIDENCE_ANSWER,
            "sources": [],
        }

    def build_response(self, state: RagAnswerState) -> RagAnswerState:
        """Graph state를 API 응답 DTO로 포장한다."""

        index_runs = normalize_index_runs(state["index_run"])
        primary_run = index_runs[0]
        # run_id는 사용자가 질문할 때 고르는 기준이 아니라 추적용 번호다.
        # 응답에는 실제 답변 기준이 된 repository_full_name, branch, commit_sha를 함께 내려준다.
        return {
            "response": RagAskResponseDTO(
                answer=state["answer"],
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
                sources=state.get("sources", []),
            )
        }


def build_sources(rows: list[VectorResultRow]) -> list[RagAskSourceDTO]:
    """LLM 답변 아래에 노출할 citation, path, 거리 정보를 검색 결과에서 추출한다."""

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
            )
        )
    return sources


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
