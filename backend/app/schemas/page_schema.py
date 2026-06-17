from datetime import date as DateType
from datetime import datetime as DateTimeType
from datetime import time as TimeType

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BlockType, PageType


# 회의/회고 본문 블록을 새로 만들 때 프론트에서 보내는 데이터 형태입니다.
# 예: 문단, 제목, 불릿, 체크리스트, 코드 블록
class BlockCreate(BaseModel):
    # 블록 종류입니다. 값이 없으면 기본값은 일반 문단입니다.
    type: BlockType = BlockType.PARAGRAPH

    # 블록 안에 들어갈 실제 텍스트 내용입니다.
    content: str = ""

    # 체크리스트 블록일 때만 체크 여부를 사용합니다.
    # 문단/제목/불릿/코드에서는 보통 None입니다.
    checked: bool | None = None


# DB에 저장된 본문 블록을 프론트로 돌려줄 때 사용하는 응답 형태입니다.
class BlockResponse(BaseModel):
    # 블록 고유 id입니다.
    id: int

    # 블록 종류입니다.
    type: BlockType

    # 블록 내용입니다.
    content: str

    # 체크리스트 완료 여부입니다.
    checked: bool | None

    # 같은 페이지 안에서 블록이 몇 번째 순서인지 나타냅니다.
    order_index: int

    # 블록 생성 시간입니다.
    created_at: DateTimeType

    # 블록 수정 시간입니다.
    updated_at: DateTimeType

    # SQLAlchemy 모델 객체를 Pydantic 응답 모델로 바로 변환할 수 있게 합니다.
    model_config = ConfigDict(from_attributes=True)


# 태그 응답 형태입니다.
# 현재 페이지 기능에서는 적극적으로 쓰이지 않을 수 있지만, 태그 기능 확장용으로 남아 있습니다.
class TagResponse(BaseModel):
    # 태그 고유 id입니다.
    id: int

    # 태그 이름입니다.
    name: str

    # 태그 생성 시간입니다.
    created_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


# 페이지 작성자 정보를 프론트로 내려줄 때 사용하는 응답 형태입니다.
# 상세/수정 모달에서 "작성자 닉네임"을 보여주기 위해 PageResponse 안에 포함됩니다.
class PageAuthorResponse(BaseModel):
    # 작성자 user id입니다.
    id: int

    # 작성자 이메일입니다.
    email: str

    # 화면에 표시할 작성자 닉네임입니다.
    nickname: str

    model_config = ConfigDict(from_attributes=True)


# 새 회의/회고 페이지를 만들 때 프론트에서 백엔드로 보내는 요청 형태입니다.
class PageCreate(BaseModel):
    # 페이지 종류입니다. MEETING 또는 RETROSPECTIVE 중 하나입니다.
    type: PageType

    # 페이지 제목입니다. 1자 이상 200자 이하만 허용합니다.
    title: str = Field(..., min_length=1, max_length=200)

    # 캘린더에서 기준이 되는 날짜입니다.
    date: DateType

    # 회의 시작 시간입니다. 회고는 보통 None입니다.
    start_time: TimeType | None = None

    # 회의 종료 시간입니다. 회고는 보통 None입니다.
    end_time: TimeType | None = None

    # 참여자 이름 목록입니다. 값이 없으면 빈 리스트가 됩니다.
    participants: list[str] = Field(default_factory=list)

    # 본문 블록 목록입니다. 값이 없으면 빈 리스트가 됩니다.
    blocks: list[BlockCreate] = Field(default_factory=list)


# 기존 회의/회고 페이지를 수정할 때 프론트에서 백엔드로 보내는 요청 형태입니다.
# 모든 필드가 선택값이라, 전달된 값만 수정할 수 있습니다.
class PageUpdate(BaseModel):
    # 수정할 제목입니다.
    title: str | None = Field(default=None, min_length=1, max_length=200)

    # 수정할 날짜입니다.
    date: DateType | None = None

    # 수정할 시작 시간입니다.
    start_time: TimeType | None = None

    # 수정할 종료 시간입니다.
    end_time: TimeType | None = None

    # 수정할 참여자 목록입니다.
    participants: list[str] | None = None

    # 수정할 본문 블록 목록입니다.
    # 이 값이 들어오면 기존 블록을 삭제하고 새 블록 목록으로 다시 저장합니다.
    blocks: list[BlockCreate] | None = None

    # AI가 생성한 요약 내용입니다.
    ai_summary: str | None = None


# 회의/회고 상세 조회, 생성 결과, 수정 결과로 프론트에 내려주는 전체 응답 형태입니다.
class PageResponse(BaseModel):
    # 페이지 고유 id입니다.
    id: int

    # 페이지 종류입니다. MEETING 또는 RETROSPECTIVE입니다.
    type: PageType

    # 페이지 제목입니다.
    title: str

    # 캘린더 기준 날짜입니다.
    date: DateType

    # 회의 시작 시간입니다.
    start_time: TimeType | None

    # 회의 종료 시간입니다.
    end_time: TimeType | None

    # 작성자 user id입니다.
    author_id: int

    # 작성자 상세 정보입니다. 닉네임 표시와 수정 권한 판단에 사용합니다.
    author: PageAuthorResponse

    # 참여자 목록입니다.
    participants: list[str]

    # AI 요약입니다. 아직 없으면 None입니다.
    ai_summary: str | None

    # 본문 블록 전체 목록입니다.
    blocks: list[BlockResponse]

    # 페이지 생성 시간입니다.
    created_at: DateTimeType

    # 페이지 마지막 수정 시간입니다.
    updated_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


# 페이지 목록 조회 API에서 한 페이지씩 내려줄 때 사용하는 간단한 응답 형태입니다.
# 상세 본문 blocks는 포함하지 않습니다.
class PageListItem(BaseModel):
    # 페이지 고유 id입니다.
    id: int

    # 페이지 종류입니다.
    type: PageType

    # 페이지 제목입니다.
    title: str

    # 캘린더 기준 날짜입니다.
    date: DateType

    # 회의 시작 시간입니다.
    start_time: TimeType | None

    # 회의 종료 시간입니다.
    end_time: TimeType | None

    # 작성자 user id입니다.
    author_id: int

    author: PageAuthorResponse

    # 참여자 목록입니다.
    participants: list[str]

    # AI 요약입니다.
    ai_summary: str | None

    # 페이지 생성 시간입니다.
    created_at: DateTimeType

    # 페이지 수정 시간입니다.
    updated_at: DateTimeType

    model_config = ConfigDict(from_attributes=True)


# 페이지 목록 조회 응답 형태입니다.
# items에는 실제 페이지 목록이 들어가고, total/page/size는 페이지네이션 정보입니다.
class PageListResponse(BaseModel):
    # 현재 페이지에 포함된 페이지 목록입니다.
    items: list[PageListItem]

    # 전체 페이지 개수입니다.
    total: int

    # 현재 페이지 번호입니다.
    page: int

    # 한 번에 가져오는 개수입니다.
    size: int


# 캘린더 화면에서 월별 회의/회고를 표시할 때 사용하는 최소 응답 형태입니다.
# 본문 전체는 필요 없고, 캘린더 태그와 오른쪽 패널 카드에 필요한 정보만 담습니다.
class CalendarPageItem(BaseModel):
    # 페이지 고유 id입니다. 상세 조회를 할 때 사용합니다.
    id: int

    # 페이지 종류입니다. 회의인지 회고인지 구분합니다.
    type: PageType

    # 오른쪽 패널 카드에 표시할 제목입니다.
    title: str

    # 캘린더에서 어느 날짜에 표시할지 결정하는 날짜입니다.
    date: DateType

    # 회의 시작 시간입니다. 회고면 보통 None입니다.
    start_time: TimeType | None

    # 회의 종료 시간입니다. 회고면 보통 None입니다.
    end_time: TimeType | None

    # 작성자 user id입니다.
    # 프론트에서 현재 로그인 사용자 id와 비교해 연필 아이콘 표시 여부를 결정합니다.
    author_id: int

    model_config = ConfigDict(from_attributes=True)
