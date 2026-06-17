from app.pipeline.domain import CODE_INDEX, REPO_SYNC
from app.workers.workers import HeartbeatWorker, SyncPollingWorker, build_worker


def test_heartbeat_worker_runs_until_stopped() -> None:
    logs: list[str] = []
    ticks = {"n": 0}

    def should_stop() -> bool:
        ticks["n"] += 1
        return ticks["n"] > 2

    worker = HeartbeatWorker(
        kind="code-index",
        interval=0,
        sleep=lambda _seconds: None,
        log=logs.append,
    )
    worker.run(should_stop)

    assert any("started" in line for line in logs)
    assert sum("heartbeat" in line for line in logs) == 2
    assert any("stopped" in line for line in logs)


def test_build_worker_returns_heartbeat_for_non_sync_kind() -> None:
    worker = build_worker(CODE_INDEX)

    assert isinstance(worker, HeartbeatWorker)
    assert worker.kind == CODE_INDEX


def test_build_worker_uses_sync_factory_for_repo_sync() -> None:
    sentinel = HeartbeatWorker(kind="stub")

    worker = build_worker(REPO_SYNC, sync_worker_factory=lambda: sentinel)

    assert worker is sentinel


def test_sync_polling_worker_delegates_to_poller() -> None:
    class _FakePoller:
        def __init__(self) -> None:
            self.received: list[object] = []

        def run_forever(self, should_stop=None) -> None:
            self.received.append(should_stop)

    poller = _FakePoller()
    worker = SyncPollingWorker(poller=poller, log=lambda _line: None)

    def stop() -> bool:
        return True

    worker.run(stop)

    assert poller.received == [stop]
