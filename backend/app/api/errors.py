from collections.abc import Callable, Mapping
from typing import TypeVar

from fastapi import HTTPException

T = TypeVar("T")
ExceptionStatuses = Mapping[type[Exception], int]


class DomainError(Exception):
    """모든 도메인 및 비즈니스 예외의 기본 클래스"""
    pass


class EntityNotFoundError(DomainError):
    """리소스를 찾을 수 없을 때 발생하는 예외"""
    pass


class DomainValidationError(DomainError):
    """비즈니스 유효성 검증 실패 시 발생하는 예외"""
    pass


class DomainConflictError(DomainError):
    """비즈니스 규칙 위반 또는 상태 충돌 시 발생하는 예외"""
    pass



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

