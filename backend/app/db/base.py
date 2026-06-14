# SQLAlchemy 공통 Base와 mixin을 정의하는 파일
# 모든 ORM model이 공통으로 사용할 id, timestamp 컬럼을 제공
from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# SQLAlchemy : Base를 상속받는 클래스들은 ORM 모델로 등록
class Base(DeclarativeBase):
    pass

## 공통 컬럼
class TimestampMixin:
    # db칼럼 이름 : 타입힌트 = 실제로 DB 컬럼을 만드는 설정
    created_at: Mapped[datetime] = mapped_column( # DB 컬럼 정의
        DateTime, # DB 타입 명시
        default = datetime.utcnow, # 기본값:현재 UTC 시간 / 함수 자체를 넘김
        nullable = False, # null 허용 여부
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        onupdate = datetime.utcnow, # 마지막 수정 시간
        nullable = False, # 수정한 적 없어도 생성 시점과 같은 값으로 채움
    )

class IdMixin:
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key = True, # 중복 불가 + NULL 불가 + 식별자 + 인덱스
        autoincrement = True,
    )
