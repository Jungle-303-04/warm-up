from sqlmodel import SQLModel

from database import engine
from models.font import Font

SQLModel.metadata.create_all(engine)

print("fonts 테이블 생성완료")