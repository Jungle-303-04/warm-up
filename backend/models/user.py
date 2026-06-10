from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    nickname: str = Field(sa_column=Column(String(20), nullable=False, unique=True))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
