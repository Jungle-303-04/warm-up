import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

POSTGRES_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

# connect to PostgreSQL server
# # Python code <-> SQLAlchemy engine <-> PostgreSQL
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