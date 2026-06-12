from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# 요청 헤더에서 토큰을 꺼내줘서 저장
# Authorization: Bearer eyJhbGciOi... -> eyJhbGciOi
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db), #db 세션 가져옴
) -> User:
    """
    Authorization: Bearer <token> 으로 들어온 JWT를 검증하고
    현재 로그인한 User를 반환한다.
    """

    #인증 실패 시 던질 에러(토큰 없거나, 토큰 만료되었거나 등등)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 올바르지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try: #토큰을 decode한다
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )


        
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    #토큰 없거나, 토큰 만료되었거나, 서명 안맞거나 등
    except JWTError:
        raise credentials_exception

    #db에서 user_id가진 유저 찾으면 반환
    user = db.execute(
        select(User).where(User.id == int(user_id))
    ).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user