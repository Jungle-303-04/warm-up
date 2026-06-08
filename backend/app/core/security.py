from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    사용자의 원본 비밀번호를 해시한다.
    DB에는 원본 비밀번호를 저장하지 않고 password_hash만 저장한다.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    로그인 시 입력한 비밀번호와 DB에 저장된 해시 비밀번호를 비교한다.
    """
    return pwd_context.verify(plain_password, hashed_password)

# subject라는 문자열을 받아서, JWT 토큰 문자열을 만들어 반환한다
def create_access_token(subject: str) -> str:
    """
    JWT access token 생성.
    subject에는 보통 user_id를 문자열로 넣는다.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject, # user_id
        "exp": expire,  # 만료시간
    }

    #토큰 만들기
    token = jwt.encode(
        payload, # 내용
        settings.JWT_SECRET_KEY, #서버만 알고 있는 비밀 키
        algorithm=settings.JWT_ALGORITHM, #서명할 때 사용할 알고리즘
    )

    return token