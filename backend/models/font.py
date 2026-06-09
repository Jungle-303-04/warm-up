from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Text

class Font(SQLModel, table=True):
    __tablename__ = "fonts"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(sa_column=Column(String(100), nullable=False))
    source: str = Field(sa_column=Column(String(50), nullable=False))
    is_paid: bool = Field(default=False, nullable=False)

    license: str = Field(sa_column=Column(String(100), nullable=False))
    category: str = Field(sa_column=Column(String(50), nullable=False))

    tags: str = Field(sa_column=Column(Text, nullable=True))
    description: str = Field(sa_column=Column(Text, nullable=True))
    weights: str = Field(sa_column=Column(Text, nullable=True))

    webfont_url: str = Field(sa_column=Column(Text, nullable=True))
    source_url: str = Field(sa_column=Column(Text, nullable=False))