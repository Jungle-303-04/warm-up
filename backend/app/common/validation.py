# 공통 검증 함수들을 모아두는 파일
# service 계층에서 필수값 누락 여부를 확인할 때 사용


# required value validation
def require_value(value: object, field_name: str) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")
