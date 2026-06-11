from enum import Enum

# 페이지 종류를 제한하는 값이다. 아무 문자열이나 들어가지 않게 막는다.
class PageType(str, Enum):
    # 회의록 페이지
    MEETING = "MEETING"
    # 회고 페이지
    RETROSPECTIVE = "RETROSPECTIVE"

# 페이지 본문 블록의 종류를 제한하는 값이다.
class BlockType(str, Enum):
    # 일반 문단
    PARAGRAPH = "PARAGRAPH"
    # 제목 블록
    HEADING = "HEADING"
    # 불릿 목록
    BULLET = "BULLET"
    # 체크리스트 항목
    CHECKLIST = "CHECKLIST"
    # 코드 블록
    CODE = "CODE"
