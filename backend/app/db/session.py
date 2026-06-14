# DB engine과 session factory를 정의하는 파일
# repository 계층에서 사용할 SQLAlchemy session을 생성
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV_PATH)

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

# connect to PostgreSQL server
# Python code <-> SQLAlchemy engine <-> PostgreSQL
engine = create_engine(POSTGRES_DATABASE_URL)

# configure a factory for creating DB sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# make DB session
def get_session() -> Session:
    with SessionLocal() as session: # open a new db session
        yield session
