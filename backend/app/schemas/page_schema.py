from datetime import date as DateType
from datetime import datetime as DateTimeType
from datetime import time as TimeType

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BlockType, PageType


class BlockCreate(BaseModel):
    type: BlockType = BlockType.PARAGRAPH
    content: str = ""
    checked: bool | None = None











class PageCreate(BaseModel):
    type: PageType
    title: str = Field(..., min_length=1, max_length=200)
    date: DateType
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    participants: list[str] = Field(default_factory=list)
    blocks: list[BlockCreate] = Field(default_factory=list)
    tags: str | None = None