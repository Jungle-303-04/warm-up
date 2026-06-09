import argparse
import asyncio
import signal

from app.pipeline import PIPELINE_STAGES, WORKER_STAGE_IDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a RepoPilot worker.")
    parser.add_argument(
        "kind",
        choices=WORKER_STAGE_IDS,
        help="Worker kind to run.",
    )
    return parser.parse_args()


async def run(kind: str) -> None:
    # 현재 worker는 queue 처리 전 placeholder라 종료 신호를 기다리며 heartbeat만 남긴다.
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame), stop_event.set)

    stage = next(stage for stage in PIPELINE_STAGES if stage.id == kind)
    print(f"RepoPilot worker started: {stage.id} - {stage.purpose}", flush=True)

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60)
        except TimeoutError:
            print(f"RepoPilot worker heartbeat: {kind}", flush=True)

    print(f"RepoPilot worker stopped: {kind}", flush=True)


def main() -> None:
    args = parse_args()
    asyncio.run(run(args.kind))


if __name__ == "__main__":
    main()
