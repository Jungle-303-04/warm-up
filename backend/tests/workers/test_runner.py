import sys

import pytest

from app.workers.runner import parse_args


def test_parse_args_accepts_worker_stage_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["runner", "repo-sync"])

    args = parse_args()

    assert args.kind == "repo-sync"


def test_parse_args_rejects_human_approval_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["runner", "approval"])

    with pytest.raises(SystemExit):
        parse_args()
