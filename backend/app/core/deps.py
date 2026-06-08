from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Authorization: Bearer <token> 으로 들어온 JWT를 검증하고
    현재 로그인한 User를 반환한다.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 올바르지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        #jwt.decode() 성공하면 payload 나온다
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        #jwt payload에서 sub값(user id)을 꺼낸다
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    #DB에서 User.id가 user_id인 사람 조회
    user = db.execute(
        select(User).where(User.id == int(user_id))
    ).scalar_one_or_none() #결과 하나만 가져오겠다

    if user is None:
        raise credentials_exception

    return user