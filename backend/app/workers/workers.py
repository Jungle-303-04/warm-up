"""백그라운드 워커 구현.

repo-sync 워커는 repo_rag의 sync 큐를 실제로 폴링·처리한다(SyncJobPoller 재사용).
나머지 단계는 아직 전용 큐가 없다 — 인덱싱/제안 파이프라인이 sync 워커 내부에서
인라인 처리되기 때문이다. 그래서 placeholder 하트비트로 동작하며, 전용 큐가 생기면
같은 자리(build_worker 분기)에 실제 워커를 추가한다.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from app.pipeline.domain.stages import REPO_SYNC

StopPredicate = Callable[[], bool]


def _never() -> bool:
    return False


class Worker(Protocol):
    def run(self, should_stop: StopPredicate | None = None) -> None: ...


@dataclass
class HeartbeatWorker:
    """전용 큐가 없는 단계의 placeholder. 살아있음만 주기적으로 알린다."""

    kind: str
    interval: float = 60.0
    sleep: Callable[[float], None] = time.sleep
    log: Callable[[str], None] = print

    def run(self, should_stop: StopPredicate | None = None) -> None:
        should_stop = should_stop or _never
        self.log(f"RepoPilot worker started (placeholder): {self.kind}")
        while not should_stop():
            self.sleep(self.interval)
            self.log(f"RepoPilot worker heartbeat: {self.kind}")
        self.log(f"RepoPilot worker stopped: {self.kind}")


@dataclass
class SyncPollingWorker:
    """repo-sync: sync 큐를 폴링해 실제 인덱싱 파이프라인을 돌린다."""

    poller: object  # SyncJobPoller: run_forever(should_stop) 보유
    log: Callable[[str], None] = print

    def run(self, should_stop: StopPredicate | None = None) -> None:
        self.log("RepoPilot worker started: repo-sync (sync 큐 폴링)")
        self.poller.run_forever(should_stop)  # type: ignore[attr-defined]
        self.log("RepoPilot worker stopped: repo-sync")


def build_worker(
    kind: str,
    *,
    sync_worker_factory: Callable[[], Worker] | None = None,
) -> Worker:
    if kind == REPO_SYNC:
        factory = sync_worker_factory or _build_sync_polling_worker
        return factory()
    return HeartbeatWorker(kind=kind)


def _build_sync_polling_worker() -> Worker:
    from app.config import get_settings
    from app.repo_rag.application.service import RepoRagSyncService
    from app.repo_rag.dependencies import build_embedding_client
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory
    from app.repo_rag.infrastructure.sql_unit_of_work import SqlUnitOfWork
    from app.repo_rag.poller import SyncJobPoller

    settings = get_settings()
    if not settings.uses_postgres or settings.postgres_database_url is None:
        raise SystemExit("repo-sync 워커는 POSTGRES_DATABASE_URL이 필요합니다")

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    service = RepoRagSyncService(
        uow_factory=uow_factory,
        embedder=build_embedding_client(settings),
    )
    return SyncPollingWorker(poller=SyncJobPoller(uow_factory, service))
