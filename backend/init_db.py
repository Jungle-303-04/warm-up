from sqlmodel import SQLModel

from database import engine

# 이 import가 실행되면 Python이 models/font.py 파일을 읽고,
# Font 클래스가 메모리에 로드됨.
# Font가 SQLModel을 상속하고 table=True이므로
# SQLModel metadata에 테이블 설계도로 등록됨.
from models.font import Font
from models.post import Post
from models.user import User

# 테이블 추가해도 create_all이 있으면 생성하고 없음 건너뜀
SQLModel.metadata.create_all(engine)