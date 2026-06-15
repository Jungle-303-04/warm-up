import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.github.infrastructure.jwt_auth import build_app_jwt


def _keypair() -> tuple[str, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def test_build_app_jwt_is_verifiable_with_public_key() -> None:
    private_pem, public_pem = _keypair()
    now = int(time.time())

    token = build_app_jwt("12345", private_pem, now=now)
    claims = jwt.decode(token, public_pem, algorithms=["RS256"])

    assert claims["iss"] == "12345"
    assert claims["iat"] == now - 60
    assert claims["exp"] == now + 540


def test_build_app_jwt_respects_github_ten_minute_limit() -> None:
    private_pem, _ = _keypair()
    now = int(time.time())

    token = build_app_jwt("12345", private_pem, now=now)
    claims = jwt.decode(token, options={"verify_signature": False})

    assert claims["exp"] - claims["iat"] <= 600
