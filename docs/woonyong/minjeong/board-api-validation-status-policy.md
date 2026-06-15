# Board API 검증 실패 상태 코드 기준

## 목적

이 문서는 `minjeong` 브랜치의 Board create API에서 검증 실패를 어떤 HTTP
status로 반환할지 정리한 기준이다. 파일명은 영어로 유지하지만, 본문은 팀
공유를 위해 한국어로 작성한다.

핵심 결론:

- 요청 body validation 실패는 `422`로 통일한다.
- 요청 자체가 깨졌거나 API 계약 이전 단계에서 잘못된 경우만 `400`으로 둔다.
- 이미 존재하거나 현재 리소스 상태와 충돌하는 경우는 `409`를 검토한다.

## 기준 요약

| 상황 | 권장 status | 이유 |
|---|---:|---|
| JSON 문법이 깨져 body를 읽을 수 없음 | `400` | 요청 형식 자체가 잘못됨 |
| `board_type`이 1, 2, 3이 아님 | `422` | 요청 body 값이 API 입력 규칙을 만족하지 못함 |
| basic board인데 detail/task가 들어옴 | `422` | body 조합 validation 실패 |
| schedule board인데 `schedule_board_detail`이 없음 | `422` | JSON은 이해했지만 필드 조합이 처리 불가능함 |
| proceedings board인데 schedule detail/task가 들어옴 | `422` | body 조합 validation 실패 |
| `start_at >= end_at` | `422` | 일정 도메인 입력 규칙 위반 |
| 인증 토큰 없음 | `401` | 인증 필요 |
| 인증은 됐지만 권한 없음 | `403` | 접근 권한 부족 |
| path의 `board_id`가 없음 | `404` | 요청한 리소스가 없음 |
| body의 참조 id가 없음 | `422` 또는 `404` | 팀 기준 필요. 이 문서에서는 body validation이면 `422`를 우선 권장 |
| 이미 존재해서 생성할 수 없음 | `409` | 현재 리소스 상태와 충돌 |

## 400과 422의 차이

`400 Bad Request`는 서버가 요청을 정상적인 API 입력으로 해석하기 전 단계에서
문제가 있는 경우에 쓴다. 예를 들어 JSON 문법이 깨졌거나, content type이 API
계약과 맞지 않거나, 요청 형식 자체가 잘못된 경우다.

`422 Unprocessable Entity`는 요청 body를 JSON으로 이해했고 필드도 읽었지만,
그 값이나 조합이 API의 입력 규칙을 만족하지 못할 때 쓴다.

Board create 기준에서는 다음을 `422`로 보는 것이 좋다.

- `board_type`이 1, 2, 3이 아님
- `board_type = 1`인데 `schedule_board_detail`, `schedule_board_tasks`,
  `proceedings_board_detail` 중 하나가 들어옴
- `board_type = 2`인데 `schedule_board_detail`이 없음
- `board_type = 2`인데 `proceedings_board_detail`이 들어옴
- `board_type = 3`인데 `proceedings_board_detail`이 없음
- `board_type = 3`인데 `schedule_board_detail` 또는 `schedule_board_tasks`가 들어옴
- `start_at >= end_at`

## FastAPI에서의 구현 방향

가능하면 요청 body 검증은 `schema.py`의 Pydantic model validator로 옮긴다.
그러면 FastAPI가 validation error를 자동으로 `422`로 반환한다.

```python
from pydantic import BaseModel, Field, model_validator

BASIC_BOARD_TYPE = 1
SCHEDULE_BOARD_TYPE = 2
PROCEEDINGS_BOARD_TYPE = 3


class CreateBoard(BaseModel):
    board_type: int
    title: str
    content: str
    tag: str | None = None
    user_id: int

    assignee_user_ids: list[int] = Field(default_factory=list)
    participant_user_ids: list[int] = Field(default_factory=list)
    carbon_copy_user_ids: list[int] = Field(default_factory=list)

    schedule_board_detail: CreateScheduleBoardDetail | None = None
    schedule_board_tasks: list[CreateScheduleBoardTaskDetail] = Field(default_factory=list)
    proceedings_board_detail: CreateProceedingsBoardDetail | None = None

    @model_validator(mode="after")
    def validate_board_detail(self):
        if self.board_type not in {
            BASIC_BOARD_TYPE,
            SCHEDULE_BOARD_TYPE,
            PROCEEDINGS_BOARD_TYPE,
        }:
            raise ValueError("invalid board_type")

        if self.board_type == BASIC_BOARD_TYPE:
            if (
                self.schedule_board_detail is not None
                or self.schedule_board_tasks
                or self.proceedings_board_detail is not None
            ):
                raise ValueError("detail fields are not allowed for basic board")

        if self.board_type == SCHEDULE_BOARD_TYPE:
            if self.schedule_board_detail is None:
                raise ValueError("schedule_board_detail is required")
            if self.proceedings_board_detail is not None:
                raise ValueError("proceedings detail is only allowed for proceedings board")
            if self.schedule_board_detail.start_at >= self.schedule_board_detail.end_at:
                raise ValueError("start_at must be earlier than end_at")

        if self.board_type == PROCEEDINGS_BOARD_TYPE:
            if self.proceedings_board_detail is None:
                raise ValueError("proceedings_board_detail is required")
            if self.schedule_board_detail is not None or self.schedule_board_tasks:
                raise ValueError("schedule fields are only allowed for schedule board")

        return self
```

## Service와 Router의 책임 분리

추천 방향:

- `schema.py`
  - 요청 body의 필드 타입, 범위, 필드 조합 검증
  - 실패 시 FastAPI 기본 `422`
- `service.py`
  - DB 조회가 필요한 비즈니스 규칙
  - 예: 이미 마감된 project에는 board 생성 불가
  - 가능하면 FastAPI `HTTPException` 대신 도메인 예외 사용
- `router.py`
  - 도메인 예외를 HTTP status로 변환
  - service 결과를 response DTO로 반환

즉, 지금 service에 있는 `HTTPException(400)` 검증은 학습 단계에서는 괜찮지만,
다음 정리 단계에서는 Pydantic validator 또는 도메인 예외로 옮기는 것이 좋다.

## 민정에게 줄 피드백 문장

> `basic` 타입을 추가해서 일반 게시글과 상세 게시글을 나누려는 방향은 좋아.
> 다만 이 검증은 요청 body validation에 가까우니까 status는 `422`로 통일하고,
> 가능하면 `schema.py`의 Pydantic validator로 옮기자. service는 DB 조회나
> 저장처럼 실제 비즈니스 처리에 집중시키면 구조가 더 깔끔해져.
