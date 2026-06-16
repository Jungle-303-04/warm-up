"""repo-rag Postgres 스키마 초기화.

실행:
    POSTGRES_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/repolm \
        python -m scripts.init_db

순서:
1. vector 확장 생성
2. SQLAlchemy 모델로 테이블과 인덱스 생성
"""

from sqlalchemy import text

from app.config import get_settings
from app.repo_rag.infrastructure import models  # noqa: F401  (모델 등록)
from app.repo_rag.infrastructure.db import Base, create_db_engine


def main() -> None:
    settings = get_settings()
    if not settings.postgres_database_url:
        raise SystemExit("POSTGRES_DATABASE_URL 환경변수가 필요합니다")

    engine = create_db_engine(settings.postgres_database_url)

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

    print("repo-rag 스키마 초기화 완료")


if __name__ == "__main__":
    main()
