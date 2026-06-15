import time

import pytest

from app.auth.infrastructure.session_tokens import SessionTokenCodec


def _codec(ttl: int = 3600) -> SessionTokenCodec:
    return SessionTokenCodec(secret="test-secret", ttl_seconds=ttl)


def test_issue_then_verify_roundtrip() -> None:
    codec = _codec()

    token = codec.issue(42, "octocat")
    claims = codec.verify(token)

    assert claims.user_id == 42
    assert claims.login == "octocat"


def test_verify_rejects_tampered_token() -> None:
    token = _codec().issue(42, "octocat")

    with pytest.raises(ValueError, match="유효하지 않은"):
        _codec().verify(token + "x")


def test_verify_rejects_wrong_secret() -> None:
    token = _codec().issue(42, "octocat")
    other = SessionTokenCodec(secret="another-secret", ttl_seconds=3600)

    with pytest.raises(ValueError):
        other.verify(token)


def test_verify_rejects_expired_token() -> None:
    codec = _codec(ttl=10)
    past = int(time.time()) - 100

    token = codec.issue(42, "octocat", now=past)

    with pytest.raises(ValueError):
        codec.verify(token)
