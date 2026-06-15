import pytest

from app.github.domain.events import parse_push_event

_PUSH = {
    "ref": "refs/heads/main",
    "after": "abc123",
    "repository": {"full_name": "o/r", "clone_url": "https://github.com/o/r.git"},
}


def test_parse_push_event_extracts_repository_and_branch() -> None:
    event = parse_push_event(_PUSH)

    assert event.repository_full_name == "o/r"
    assert event.repository_url == "https://github.com/o/r.git"
    assert event.branch == "main"
    assert event.commit_sha == "abc123"


def test_parse_non_branch_ref_raises() -> None:
    with pytest.raises(ValueError, match="브랜치 push"):
        parse_push_event({"ref": "refs/tags/v1", "repository": {}})


def test_parse_missing_repository_raises() -> None:
    with pytest.raises(ValueError, match="repository 정보"):
        parse_push_event({"ref": "refs/heads/main"})
