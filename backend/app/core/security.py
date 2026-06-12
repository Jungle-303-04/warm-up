from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    회원가입 때 사용한다.
    원본 비밀번호를 DB에 저장하지 않고 해시값으로 바꾼다.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    로그인 때 사용한다.
    사용자가 입력한 비밀번호와 DB의 password_hash를 비교한다.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str: #subject 유저 id ex) 3이면
    """
    JWT access token을 만든다.
    subject에는 user.id를 문자열로 넣는다.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expire,
    }

    # 1. header를 만든다
    # 2. payload를 JSON으로 바꾼다
    # 3. header와 payload를 Base64URL 형태로 인코딩한다
    # 4. secret key와 algorithm으로 서명(signature)을 만든다
    # 5. header.payload.signature 형태로 합친다
    token = jwt.encode( # 결과물 : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token