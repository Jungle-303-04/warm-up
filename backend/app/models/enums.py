from enum import Enum


# 페이지가 어떤 종류의 문서인지 제한하는 값 목록이다.
class PageType(str, Enum):
    MEETING = "MEETING"
    RETROSPECTIVE = "RETROSPECTIVE"


# 페이지 안의 블록이 어떤 형태인지 제한하는 값 목록이다.
class BlockType(str, Enum):
    PARAGRAPH = "PARAGRAPH"
    HEADING = "HEADING"
    BULLET = "BULLET"
    CHECKLIST = "CHECKLIST"
    CODE = "CODE"
