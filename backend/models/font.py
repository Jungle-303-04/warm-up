from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Text, JSON


class Font(SQLModel, table=True):
    __tablename__ = "fonts"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(sa_column=Column(String(100), nullable=False))
    source: str = Field(sa_column=Column(String(50), nullable=False))
    is_paid: bool = Field(default=False, nullable=False)

    license: str | None = Field(default=None, sa_column=Column(Text))
   
    category: str | None = Field(default=None, sa_column=Column(String(50), nullable=True))

    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    weights: list[int] = Field(default_factory=list,sa_column=Column(JSON))

    download_url : str | None = Field(default=None, sa_column=Column(Text))
    source_url: str = Field(sa_column=Column(Text, nullable=False))

    license_summary: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    webfonts: list[dict] = Field(default_factory=list, sa_column=Column(JSON))