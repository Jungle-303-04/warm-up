import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlmodel import SQLModel, Session, select

from database import engine
from models.font import Font
from models.post import Post
from models.user import User

router = APIRouter(prefix="/auth")

ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 1


class AuthRequest(SQLModel):
    nickname: str
    password: str


class UserRead(SQLModel):
    id: int
    nickname: str


class AuthResponse(SQLModel):
    user: UserRead


class TokenPayload(SQLModel):
    user_id: int
    token_type: str


def get_jwt_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY 환경변수가 설정되어 있지 않습니다.",
        )

    return secret_key


def get_access_token_expire_minutes() -> int:
    expire_minutes = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    if expire_minutes is None:
        return DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

    return int(expire_minutes)


def get_refresh_token_expire_days() -> int:
    expire_days = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")

    if expire_days is None:
        return DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS

    return int(expire_days)


def should_use_secure_cookie() -> bool:
    cookie_secure = os.getenv("COOKIE_SECURE", "false")
    return cookie_secure.lower() == "true"


def get_cookie_samesite() -> str:
    return os.getenv("COOKIE_SAMESITE", "lax")


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")
    password_hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, password_hash_bytes)


def create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    expire_at = now + expires_delta

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": expire_at,
    }

    return jwt.encode(payload, get_jwt_secret_key(), algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_token_type: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, get_jwt_secret_key(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    token_type = payload.get("type")
    user_id = payload.get("sub")

    if token_type != expected_token_type or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
        )

    return TokenPayload(user_id=int(user_id), token_type=token_type)


def build_user_response(user: User) -> UserRead:
    return UserRead(id=user.id, nickname=user.nickname)


def find_user_by_nickname(session: Session, nickname: str) -> Optional[User]:
    statement = select(User).where(User.nickname == nickname)
    return session.exec(statement).first()


def get_current_user_from_access_token(request: Request) -> User:
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    token_payload = decode_token(access_token, expected_token_type="access")

    with Session(engine) as session:
        user = session.get(User, token_payload.user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
            )

        return user


def set_auth_cookies(response: Response, user_id: int) -> None:
    access_token = create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=get_access_token_expire_minutes()),
    )
    refresh_token = create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=get_refresh_token_expire_days()),
    )

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=should_use_secure_cookie(),
        samesite=get_cookie_samesite(),
        max_age=get_access_token_expire_minutes() * 60,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=should_use_secure_cookie(),
        samesite=get_cookie_samesite(),
        max_age=get_refresh_token_expire_days() * 24 * 60 * 60,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        httponly=True,
        secure=should_use_secure_cookie(),
        samesite=get_cookie_samesite(),
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        httponly=True,
        secure=should_use_secure_cookie(),
        samesite=get_cookie_samesite(),
    )


@router.post("/signup", response_model=AuthResponse)
def signup(auth_data: AuthRequest, response: Response):
    nickname = auth_data.nickname.strip()
    password = auth_data.password.strip()

    if not nickname:
        raise HTTPException(status_code=400, detail="닉네임은 필수 입력 항목입니다.")

    if not password:
        raise HTTPException(status_code=400, detail="패스워드는 필수 입력 항목입니다.")

    with Session(engine) as session:
        existing_user = find_user_by_nickname(session, nickname)

        if existing_user is not None:
            raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")

        user = User(nickname=nickname, password_hash=hash_password(password))

        session.add(user)
        session.commit()
        session.refresh(user)

        set_auth_cookies(response, user.id)

        return AuthResponse(user=build_user_response(user))


@router.post("/login", response_model=AuthResponse)
def login(auth_data: AuthRequest, response: Response):
    nickname = auth_data.nickname.strip()
    password = auth_data.password.strip()

    if not nickname or not password:
        raise HTTPException(status_code=400, detail="닉네임과 패스워드를 입력해주세요.")

    with Session(engine) as session:
        user = find_user_by_nickname(session, nickname)

        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="닉네임 또는 패스워드가 올바르지 않습니다.")

        set_auth_cookies(response, user.id)

        return AuthResponse(user=build_user_response(user))


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    if refresh_token is None:
        raise HTTPException(status_code=401, detail="다시 로그인이 필요합니다.")

    token_payload = decode_token(refresh_token, expected_token_type="refresh")

    with Session(engine) as session:
        user = session.get(User, token_payload.user_id)

        if user is None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

        set_auth_cookies(response, user.id)

        return AuthResponse(user=build_user_response(user))


@router.get("/me", response_model=AuthResponse)
def get_me(request: Request):
    user = get_current_user_from_access_token(request)
    return AuthResponse(user=build_user_response(user))


@router.get("/me/board")
def get_my_board(request: Request):
    user = get_current_user_from_access_token(request)

    with Session(engine) as session:
        statement = (
            select(Post)
            .where(Post.user_id == user.id)
            .order_by(Post.created_at.desc())
        )
        posts = session.exec(statement).all()

        my_posts = []
        used_font_map = {}

        for post in posts:
            font = session.get(Font, post.font_id)
            font_name = font.name if font is not None else "Unknown"

            post_summary = {
                "id": post.id,
                "title": post.title,
                "font": {
                    "id": post.font_id,
                    "name": font_name,
                },
            }
            my_posts.append(post_summary)

            if font_name not in used_font_map:
                used_font_map[font_name] = {
                    "font_name": font_name,
                    "posts": [],
                }

            used_font_map[font_name]["posts"].append({
                "id": post.id,
                "title": post.title,
            })

        return {
            "posts": my_posts,
            "used_fonts": list(used_font_map.values()),
        }


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookies(response)

    return {
        "success": True,
        "message": "로그아웃 완료",
    }
