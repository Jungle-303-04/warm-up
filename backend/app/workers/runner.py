import argparse
import asyncio
import signal

from app.pipeline import PIPELINE_STAGES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a RepoPilot worker.")
    parser.add_argument(
        "kind",
        choices=[stage["id"] for stage in PIPELINE_STAGES],
        help="Worker kind to run.",
    )
    return parser.parse_args()


async def run(kind: str) -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame), stop_event.set)

    stage = next(stage for stage in PIPELINE_STAGES if stage["id"] == kind)
    print(f"RepoPilot worker started: {stage['id']} - {stage['purpose']}", flush=True)

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

