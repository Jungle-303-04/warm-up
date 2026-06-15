from app.github.domain.signature import compute_signature, verify_signature

SECRET = "topsecret"
PAYLOAD = b'{"ref": "refs/heads/main"}'


def test_verify_accepts_matching_signature() -> None:
    header = compute_signature(SECRET, PAYLOAD)

    assert verify_signature(SECRET, PAYLOAD, header) is True


def test_verify_rejects_wrong_secret() -> None:
    header = compute_signature("other", PAYLOAD)

    assert verify_signature(SECRET, PAYLOAD, header) is False


def test_verify_rejects_tampered_payload() -> None:
    header = compute_signature(SECRET, PAYLOAD)

    assert verify_signature(SECRET, b'{"ref": "refs/heads/evil"}', header) is False


def test_verify_rejects_missing_header() -> None:
    assert verify_signature(SECRET, PAYLOAD, None) is False
    assert verify_signature(SECRET, PAYLOAD, "") is False
