def require_value(value: object, field_name: str) -> None:
    """필수 값 검증 메시지를 한 줄로 통일해 도메인 검증 코드를 짧게 유지한다."""

    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")
