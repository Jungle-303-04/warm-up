# User 테이블과 연결되는 SQLAlchemy 모델을 정의하는 파일
# 현재 board API 테스트용 기본 user 생성에 사용
from app.db.base import Base, IdMixin


# user model
class User(Base, IdMixin):
    __tablename__ = "user"
