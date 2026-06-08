from sqlalchemy import Column, ForeignKey, Table

from app.core.database import Base


page_tags = Table(
    "page_tags",
    Base.metadata,
    Column(
        "page_id",
        ForeignKey("pages.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)