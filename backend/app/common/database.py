from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.api.errors import EntityNotFoundError

ModelT = TypeVar("ModelT")


def get_or_raise[ModelT](
    session: Session,
    model: type[ModelT],
    entry_id: Any,
    error_msg: str | None = None,
) -> ModelT:
    """데이터베이스에서 엔티티를 조회하며, 없을 경우 EntityNotFoundError를 던집니다."""
    db_obj = session.get(model, entry_id)
    if db_obj is None:
        raise EntityNotFoundError(
            error_msg or f"{model.__name__} (ID: {entry_id})을(를) 찾을 수 없습니다."
        )
    return db_obj
