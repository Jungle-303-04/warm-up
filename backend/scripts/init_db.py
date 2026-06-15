"""repo-rag Postgres 스키마 초기화.

실행:
    POSTGRES_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/repopilot \
        python -m scripts.init_db

순서:
1. vector 확장 생성
2. SQLAlchemy 모델로 테이블 생성
3. sql/001_repo_rag_indexes.sql 의 인덱스(HNSW/GIN) 생성
"""

from pathlib import Path

from sqlalchemy import text

from app.config import get_settings
from app.repo_rag.infrastructure import models  # noqa: F401  (모델 등록)
from app.repo_rag.infrastructure.db import Base, create_db_engine

INDEX_SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "001_repo_rag_indexes.sql"


def main() -> None:
    settings = get_settings()
    if not settings.postgres_database_url:
        raise SystemExit("POSTGRES_DATABASE_URL 환경변수가 필요합니다")

    engine = create_db_engine(settings.postgres_database_url)

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.create_all(bind=engine)

    statements = _load_sql_statements(INDEX_SQL_PATH)
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    print("repo-rag 스키마 초기화 완료")


def _load_sql_statements(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if not line.strip().startswith("--")]
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


if __name__ == "__main__":
    main()
