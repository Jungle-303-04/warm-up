import hashlib


def hash_text(value: str) -> str:
    """텍스트 내용이 같으면 항상 같은 식별자를 만들기 위한 공통 해시 함수."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
