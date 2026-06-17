"""노트북 인프라스트럭처의 공통 유틸리티 모듈."""

def coerce_text(content: object) -> str:
    """객체를 문자열로 안전하게 변환합니다. 리스트인 경우 줄바꿈으로 병합합니다."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(part) for part in content)
    return str(content)
