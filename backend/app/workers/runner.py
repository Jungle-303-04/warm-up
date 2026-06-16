import argparse
import signal
import threading

from app.pipeline import WORKER_IDS
from app.workers.workers import build_worker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a RepoLM worker.")
    parser.add_argument(
        "kind",
        choices=WORKER_IDS,
        help="Worker kind to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    worker = build_worker(args.kind)

    stop = threading.Event()
    for signame in ("SIGINT", "SIGTERM"):
        signal.signal(getattr(signal, signame), lambda *_: stop.set())

    worker.run(should_stop=stop.is_set)


if __name__ == "__main__":
    main()
