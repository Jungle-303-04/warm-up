from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def db_transaction(db: Session) -> Generator[None, None, None]:
    """저장소 메서드가 성공 시 commit, 실패 시 rollback 규칙을 반복 작성하지 않게 한다."""

    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
