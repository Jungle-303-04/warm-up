# 공통 식별자 생성에 사용하는 유틸 파일
# 텍스트 기반 hash 값을 만들어 chunk, snapshot 같은 데이터 식별에 사용
from hashlib import sha256


# text -> sha256 hash
def hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()
