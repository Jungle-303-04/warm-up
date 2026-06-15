from datetime import date as DateType

from pydantic import BaseModel, Field

from app.models.enums import PageType


class RagQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="저장된 회의/회고 기록에 대해 질문할 내용",
    )


class RagReference(BaseModel):
    page_id: int
    title: str
    date: DateType
    type: PageType
    chunk_index: int
    distance: float


class RagQueryResponse(BaseModel):
    answer: str
    references: list[RagReference]
