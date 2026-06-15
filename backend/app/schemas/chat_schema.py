from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # 기존 채팅방에 이어서 질문할 때 사용하는 채팅방 ID.
    # 값이 없으면 백엔드에서 새 채팅방을 만든다.
    session_id: int | None = None

    # 사용자가 입력한 질문 내용.
    # 빈 문자열은 막고, 너무 긴 질문도 제한한다.
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


class ChatReference(BaseModel):
    # AI 답변을 만들 때 참고한 page ID.
    page_id: int

    # 참고한 page 제목.
    title: str

    # 참고한 page 날짜.
    # 날짜가 없는 기록일 수 있어서 None을 허용한다.
    date: str | None = None


class ChatResponse(BaseModel):
    # 이번 질문/답변이 저장된 채팅방 ID.
    # 새 채팅방이 생성된 경우 프론트는 이 값을 다음 요청의 session_id로 사용한다.
    session_id: int

    # AI가 생성한 답변 내용.
    message: str

    # 답변 생성에 사용된 참고 기록 목록.
    # 참고 기록이 없으면 빈 리스트로 내려간다.
    references: list[ChatReference] = Field(default_factory=list)
