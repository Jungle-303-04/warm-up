"""DB 폴링 기반 sync 워커 (Postgres 전용).

sync_jobs를 폴링해 queued job을 FOR UPDATE SKIP LOCKED로 클레임하고,
RepoRagSyncService.process로 처리한다(실패 시 별도 트랜잭션으로 감사 기록).

실행:
    POSTGRES_DATABASE_URL=... python -m app.repo_rag.poller
"""

import contextlib
import time
from collections.abc import Callable

from app.repo_rag.application.service import RepoRagSyncService
from app.repo_rag.application.types import UowFactory


from app.repo_rag.application.worker_stages import PipelineStageProcessor

class StageJobPoller:
    def __init__(
        self,
        uow_factory: UowFactory,
        processor: PipelineStageProcessor,
        *,
        idle_sleep: float = 2.0,
    ) -> None:
        self._uow_factory = uow_factory
        self._processor = processor
        self._idle_sleep = idle_sleep

    def run_once(self) -> str | None:
        with self._uow_factory() as uow:
            claimed = uow.repo_rag.claim_next_job_by_status(self._processor.target_status)
        if claimed is None:
            return None

        with contextlib.suppress(Exception):
            with self._uow_factory() as uow:
                self._processor.process(claimed.id, uow)
        return claimed.id

    def run_forever(self, should_stop: Callable[[], bool] | None = None) -> None:
        try:
            while should_stop is None or not should_stop():
                if self.run_once() is None:
                    time.sleep(self._idle_sleep)
        except KeyboardInterrupt:
            pass


class SyncJobPoller(StageJobPoller):
    def __init__(
        self,
        uow_factory: UowFactory,
        service: RepoRagSyncService,
        *,
        idle_sleep: float = 2.0,
    ) -> None:
        from app.repo_rag.application.worker_stages import RepoSyncStageProcessor
        processor = RepoSyncStageProcessor()
        super().__init__(uow_factory, processor, idle_sleep=idle_sleep)


def main() -> None:
    from app.config import get_settings
    from app.repo_rag.dependencies import build_embedding_client
    from app.repo_rag.infrastructure.db import create_db_engine, create_session_factory
    from app.repo_rag.infrastructure.sql_unit_of_work import SqlUnitOfWork

    settings = get_settings()
    if not settings.uses_postgres or settings.postgres_database_url is None:
        raise SystemExit("POSTGRES_DATABASE_URL 환경변수가 필요합니다")

    session_factory = create_session_factory(create_db_engine(settings.postgres_database_url))

    def uow_factory() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    service = RepoRagSyncService(uow_factory=uow_factory, embedder=build_embedding_client(settings))
    print("repo-rag sync 워커를 시작합니다", flush=True)
    SyncJobPoller(uow_factory, service).run_forever()


if __name__ == "__main__":
    main()
