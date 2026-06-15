"""GitHub 웹훅 서명 검증 (순수 로직).

GitHub은 webhook 본문을 webhook secret으로 HMAC-SHA256 서명해
`X-Hub-Signature-256: sha256=<hex>` 헤더로 보낸다. 타이밍 공격을 피하려
hmac.compare_digest로 상수시간 비교한다.
"""

import hashlib
import hmac

SIGNATURE_PREFIX = "sha256="


def compute_signature(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False
    expected = compute_signature(secret, payload)
    return hmac.compare_digest(expected, signature_header)
