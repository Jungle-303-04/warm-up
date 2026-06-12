
#API 요청 / 응답 검증용

from datetime import datetime as DateTimeType

from pydantic import BaseModel, ConfigDict, Field

#회원가입 요청 데이터 형식
class UserCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255) # ... -> 필수값
    password: str = Field(..., min_length=4, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=50)

#로그인 요청 데이터 형식
class UserLogin(BaseModel):
    email: str
    password: str

#클라이언트에게 유저 정보를 이 형태로 보내겠다
class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    created_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)

#로그인 성공했을 떄 클라에게 돌려줄 응답 형식
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" #기본 타입