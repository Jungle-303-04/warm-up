import sys

import pytest

from app.pipeline import APPROVAL, REPO_SYNC
from app.workers.runner import parse_args


def test_parse_args_accepts_worker_stage_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["runner", REPO_SYNC])

    args = parse_args()

    assert args.kind == REPO_SYNC


def test_parse_args_rejects_human_approval_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["runner", APPROVAL])

    with pytest.raises(SystemExit):
        parse_args()
