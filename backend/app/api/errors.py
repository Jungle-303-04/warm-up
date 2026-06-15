from collections.abc import Callable, Mapping
from typing import TypeVar

from fastapi import HTTPException

T = TypeVar("T")
ExceptionStatuses = Mapping[type[Exception], int]


def http_error[T](action: Callable[[], T], errors: ExceptionStatuses) -> T:
    try:
        return action()
    except Exception as exc:
        for error_type, status_code in errors.items():
            if isinstance(exc, error_type):
                raise HTTPException(
                    status_code=status_code,
                    detail=str(exc),
                ) from exc
        raise
