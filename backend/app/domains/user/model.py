from app.db.base import Base, IdMixin

class User(Base, IdMixin):
    __tablename__ = "user"