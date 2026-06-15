"""Unit of Work — 트랜잭션 경계를 컨텍스트매니저로 표현한다.

    with uow_factory() as uow:
        uow.repo_rag.create_job(...)
        uow.repo_rag.upsert_chunks(...)
    # 블록 정상 종료 → commit, 예외 → rollback

데코레이터 대신 `with` 블록으로 경계가 코드에 드러나는 게 파이썬다운 방식이다.
한 uow 안의 모든 저장소 호출은 같은 세션/트랜잭션을 공유한다.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from app.repo_rag.domain.ports import RepoRagStore


class UnitOfWork(Protocol):
    @property
    def repo_rag(self) -> RepoRagStore: ...

    @property
    def session(self) -> Any: ...  # 원시 세션(리트리버 등 어댑터가 필요로 함). in-memory는 None.

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...


@dataclass(slots=True)
class InMemoryUnitOfWork:
    """in-memory 저장소용 no-op UoW (트랜잭션 개념 없음)."""

    _repo_rag: RepoRagStore
    _session: Any = None

    @property
    def repo_rag(self) -> RepoRagStore:
        return self._repo_rag

    @property
    def session(self) -> Any:
        return self._session

    def __enter__(self) -> "InMemoryUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None
