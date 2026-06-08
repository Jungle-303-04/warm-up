from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user_schema import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=UserResponse, # 반환해야 하는 값
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: UserCreate, # 클라가 보내야 하는 값
    db: Session = Depends(get_db),
):
    # db에서 결과 1개면 -> 그 user 객체 반환
    #       결과 2개면 -> 에러
    #       결과 0개면 -> None 반환
    existing_user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )

    #DB에 저장하려면 User 데이터 객체 생성해야 함
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password), #비밀번호 해시화
        nickname=payload.nickname,
    )

    db.add(user)
    db.commit() # 실제 DB에 저장
    db.refresh(user) #DB에서 자동으로 만들어주는 값을 포함해서 user를 업데이트

    return user #위에 있는 UserResponse 필드만 골라서 보낸다

#클라가 보낸 이메일/비밀번호 확인하고, 맞으면 로그인 토큰 발급
@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    #DB에서 이메일로 유저 찾기
    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    #이메일에 해당하는 유저 없는가? OR 비밀번호가 틀렸는가?
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    #로그인에 성공하면 JWT 만든다
    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

# 현재 로그인한 내 정보 조회
@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user