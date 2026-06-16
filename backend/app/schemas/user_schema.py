from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# 회원가입할 때 프론트에서 백엔드로 보내는 요청 데이터 형태입니다.
class UserCreate(BaseModel):
    # 로그인에 사용할 이메일입니다.
    # 너무 짧거나 너무 긴 값을 막기 위해 길이 제한을 둡니다.
    email: str = Field(..., min_length=3, max_length=255)

    # 회원가입할 때 입력하는 비밀번호입니다.
    # DB에는 이 원문이 저장되지 않고, 해시된 값이 저장됩니다.
    password: str = Field(..., min_length=4, max_length=100)

    # 화면에 표시할 사용자 닉네임입니다.
    nickname: str = Field(..., min_length=1, max_length=50)


# 로그인할 때 프론트에서 백엔드로 보내는 요청 데이터 형태입니다.
class UserLogin(BaseModel):
    # 로그인할 이메일입니다.
    email: str

    # 로그인할 비밀번호입니다.
    # 백엔드는 이 값을 DB의 password_hash와 검증합니다.
    password: str


# 사용자 정보를 프론트로 내려줄 때 사용하는 응답 데이터 형태입니다.
# 회원가입 성공 응답, /auth/me 응답 등에 사용됩니다.
class UserResponse(BaseModel):
    # 사용자 고유 id입니다.
    id: int

    # 사용자 이메일입니다.
    email: str

    # 사용자 닉네임입니다.
    nickname: str

    # 사용자 계정 생성 시간입니다.
    created_at: datetime

    # SQLAlchemy User 모델 객체를 Pydantic 응답 모델로 바로 변환할 수 있게 합니다.
    model_config = ConfigDict(from_attributes=True)


# 로그인 성공 시 프론트로 내려주는 토큰 응답 형태입니다.
class TokenResponse(BaseModel):
    # 실제 JWT access token 값입니다.
    # 프론트는 이 값을 localStorage에 저장하고 이후 API 요청 헤더에 붙입니다.
    access_token: str

    # 토큰 인증 방식입니다.
    # Authorization 헤더에 "Bearer <access_token>" 형태로 보내라는 뜻입니다.
    token_type: str = "bearer"
