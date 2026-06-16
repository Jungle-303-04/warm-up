from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.page_schema import PageAuthorResponse


# 오늘의 한마디를 새로 작성할 때 프론트가 보내는 요청 데이터다.
class DailyMessageCreate(BaseModel):
    # 한마디 본문이다. 너무 짧거나 너무 길지 않도록 길이를 제한한다.
    content: str = Field(..., min_length=1, max_length=500)


# 이미 작성한 오늘의 한마디를 수정할 때 프론트가 보내는 요청 데이터다.
class DailyMessageUpdate(BaseModel):
    # 수정 후 저장할 새 본문이다.
    content: str = Field(..., min_length=1, max_length=500)


# 백엔드가 프론트로 돌려주는 오늘의 한마디 응답 데이터다.
class DailyMessageResponse(BaseModel):
    id: int
    author_id: int
    # 작성자 닉네임을 화면에 보여줘야 하므로 author 정보도 함께 내려준다.
    author: PageAuthorResponse
    content: str
    created_at: datetime
    updated_at: datetime

    # SQLAlchemy 모델 객체를 Pydantic 응답 모델로 바로 변환할 수 있게 한다.
    model_config = ConfigDict(from_attributes=True)
