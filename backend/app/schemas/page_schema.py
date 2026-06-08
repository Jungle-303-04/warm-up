from datetime import date as DateType
from datetime import datetime as DateTimeType
from datetime import time as TimeType

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BlockType, PageType


class BlockCreate(BaseModel):
    type: BlockType = BlockType.PARAGRAPH
    content: str = ""
    checked: bool | None = None


class BlockResponse(BaseModel):
    id: int
    type: BlockType
    content: str
    checked: bool | None
    order_index: int
    created_at: DateTimeType
    updated_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


class TagResponse(BaseModel):
    id: int
    name: str
    created_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


class PageCreate(BaseModel):
    type: PageType
    title: str = Field(..., min_length=1, max_length=200)
    date: DateType
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    participants: list[str] = Field(default_factory=list)
    blocks: list[BlockCreate] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    date: DateType | None = None
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    participants: list[str] | None = None
    blocks: list[BlockCreate] | None = None
    tags: list[str] | None = None
    ai_summary: str | None = None


class PageResponse(BaseModel):
    id: int
    type: PageType
    title: str
    date: DateType
    start_time: TimeType | None
    end_time: TimeType | None
    author_id: int
    participants: list[str]
    ai_summary: str | None
    blocks: list[BlockResponse]
    tags: list[TagResponse]
    created_at: DateTimeType
    updated_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


class PageListItem(BaseModel):
    id: int
    type: PageType
    title: str
    date: DateType
    start_time: TimeType | None
    end_time: TimeType | None
    author_id: int
    participants: list[str]
    ai_summary: str | None
    tags: list[TagResponse]
    created_at: DateTimeType
    updated_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


class PageListResponse(BaseModel):
    items: list[PageListItem]
    total: int
    page: int
    size: int


class CalendarPageItem(BaseModel):
    id: int
    type: PageType
    title: str
    date: DateType
    start_time: TimeType | None
    end_time: TimeType | None

    model_config = ConfigDict(from_attributes=True)