from urllib.parse import parse_qs, urlparse

from app.auth.domain.oauth import build_authorize_url, generate_state, verify_state


def test_build_authorize_url_includes_required_params() -> None:
    url = build_authorize_url(
        client_id="cid",
        redirect_uri="http://localhost:8000/auth/github/callback",
        scope="read:user repo",
        state="st4te",
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "github.com"
    assert query["client_id"] == ["cid"]
    assert query["redirect_uri"] == ["http://localhost:8000/auth/github/callback"]
    assert query["scope"] == ["read:user repo"]
    assert query["state"] == ["st4te"]


def test_generate_state_is_unique() -> None:
    assert generate_state() != generate_state()


def test_verify_state_matches_and_rejects() -> None:
    assert verify_state("abc", "abc") is True
    assert verify_state("abc", "xyz") is False
    assert verify_state("abc", None) is False
