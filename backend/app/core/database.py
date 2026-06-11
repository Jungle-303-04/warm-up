from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

#DB 작업 단위
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    #DB 세션 만든다, 실제 db에 sql을 보내는 통로 역할을 하는 객체
    db = SessionLocal()
    #API 함수에 db 빌려준다
    try:
        yield db
    #API 처리 끝나면 db 닫는다
    finally:
        db.close()