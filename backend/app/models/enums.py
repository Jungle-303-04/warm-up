from enum import Enum


class PageType(str, Enum):
    MEETING = "MEETING"
    RETROSPECTIVE = "RETROSPECTIVE"


class BlockType(str, Enum):
    PARAGRAPH = "PARAGRAPH"
    HEADING = "HEADING"
    BULLET = "BULLET"
    CHECKLIST = "CHECKLIST"
    CODE = "CODE"