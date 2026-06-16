from datetime import date as DateType

from pydantic import BaseModel, Field

from app.models.enums import PageType


# RAG 챗봇에게 질문할 때 프론트에서 백엔드로 보내는 요청 데이터 형태입니다.
class RagQueryRequest(BaseModel):
    # 사용자가 입력한 질문입니다.
    # 빈 문자열은 허용하지 않고, 너무 긴 질문도 막기 위해 최대 길이를 둡니다.
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="저장된 회의/회고 기록에 대해 질문할 내용",
    )


# RAG 답변을 만들 때 참고한 회의/회고 기록 정보를 프론트로 내려주는 형태입니다.
# 프론트에서는 답변 아래 "참고 기록" 목록을 보여줄 때 사용합니다.
class RagReference(BaseModel):
    # 참고한 페이지 id입니다.
    # 이 id로 해당 회의/회고 상세 페이지를 다시 조회할 수 있습니다.
    page_id: int

    # 참고한 회의/회고 제목입니다.
    title: str

    # 참고한 회의/회고 날짜입니다.
    date: DateType

    # 참고한 페이지 종류입니다. MEETING 또는 RETROSPECTIVE입니다.
    type: PageType

    # 한 페이지가 여러 chunk로 나뉘었을 때 몇 번째 chunk인지 나타냅니다.
    chunk_index: int

    # 질문 embedding과 참고 chunk embedding 사이의 거리입니다.
    # cosine distance 기준이라 값이 낮을수록 더 관련이 높습니다.
    distance: float


# RAG 챗봇 질문에 대한 백엔드 응답 데이터 형태입니다.
class RagQueryResponse(BaseModel):
    # AI가 생성한 최종 답변입니다.
    answer: str

    # 답변 생성에 사용된 참고 기록 목록입니다.
    references: list[RagReference]
