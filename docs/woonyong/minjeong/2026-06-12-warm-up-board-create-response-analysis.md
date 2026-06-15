# 2026-06-12 warm-up Board 생성 응답 흐름 분석

## 범위

- 사람: [민정](./README.md)
- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`minjeong`](https://github.com/Jungle-303-04/warm-up/tree/minjeong)
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: [`daeb3c0`](https://github.com/Jungle-303-04/warm-up/commit/daeb3c06c6cf99ed682e095a96743ef1a5cd4843)
- 커밋 메시지: `chore: clean up database session comments`
- 확인 시각: `2026-06-12 22:05:33 +09:00`
- 시각 자료: [Board 클래스 UML](./class-uml.md)

## 하루 요약

민정은 전날 만든 `POST /board/` create route를 한 단계 더 밀어, 요청 DTO뿐
아니라 응답 DTO와 Router -> Service -> Repository 반환 흐름까지 연결했다.
이후 service 계층에 `board_type`별 detail 필수 여부, 서로 다른 detail 조합
금지, 일정 시간 순서 검증을 추가했고, 13:19 커밋에서 `basic board` 타입을
추가해 일반 게시글은 detail/task를 받지 않도록 막았다. 21:50 이후에는
`backend/app/db/session.py`를 추가해 SQLAlchemy engine/session factory를
만들기 시작했다.

중요한 점은 실제 DB insert가 구현된 것은 아니라는 점이다. `repository.py`는
새로 생겼지만, 현재는 `datetime.utcnow()`로 시간을 만들고 고정 `id=1`인
`BoardResponse`를 반환하는 stub이다. 그래도 전날의 `return 1`보다 한 단계
좋아졌다. 이제 API 응답 형태가 코드로 명확해졌기 때문이다.

## 시간대별 작업 흐름

### 01:21 - `905283a feat: add board create response flow`

변경 파일:

- `backend/app/domains/board/schema.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/service.py`
- `backend/app/domains/board/repository.py`

구현 내용:

- `schema.py`
  - 기존 create DTO 아래에 response DTO를 추가했다.
  - `ResponseScheduleBoardDetail`
  - `ResponseScheduleBoardTaskDetail`
  - `ResponseProceedingsBoardDetail`
  - `BoardResponse`
- `router.py`
  - `response_model=BoardResponse`를 추가했다.
  - service 결과가 `None`이면 500을 반환하는 흐름을 유지했다.
  - 성공 시 dict 메시지가 아니라 `BoardResponse` 객체를 반환한다.
- `service.py`
  - 반환 타입을 `int`에서 `BoardResponse`로 바꿨다.
  - `repository.insert_board(request)`를 호출한다.
- `repository.py`
  - `insert_board(request: CreateBoard) -> BoardResponse`를 추가했다.
  - 아직 실제 DB insert는 없다.
  - `id=1`, 현재 UTC 시간, 요청 값을 조합해 `BoardResponse`를 만들어 반환한다.

### 11:27 - `2a8476a feat: add board type validation in service`

`service.py`에 Board 생성 전 도메인 검증을 추가했다.

- `SCHEDULE_BOARD_TYPE = 1`
- `PROCEEDINGS_BOARD_TYPE = 2`
- 지원하지 않는 `board_type`이면 `400 invalid board_type`
- schedule board일 때:
  - `schedule_board_detail`이 없으면 400
  - `proceedings_board_detail`이 있으면 400
  - `start_at >= end_at`이면 400
- proceedings board일 때:
  - `proceedings_board_detail`이 없으면 400
  - `schedule_board_detail` 또는 `schedule_board_tasks`가 있으면 400

이 작업에서 보이는 판단:

- 이전에 남아 있던 `board_type`과 detail 조합 불일치 위험을 직접 줄이려 했다.
- `board_type` 정수값을 상수 이름으로 빼서 의미를 조금 더 드러냈다.
- 단순 DTO 필드 검증을 넘어, 여러 필드가 함께 맞아야 하는 도메인 검증을
  service 계층에 두기 시작했다.

### 13:19 - `1e8a549 feat: support basic board type validation`

Board type 체계를 `basic`, `schedule`, `proceedings` 3종으로 다시 맞췄다.

- `model.py`
  - `BASIC_BOARD_TYPE = 1`
  - `SCHEDULE_BOARD_TYPE = 2`
  - `PROCEEDINGS_BOARD_TYPE = 3`
  - 주석의 schedule/proceedings 번호를 각각 2, 3으로 변경했다.
- `schema.py`
  - `CreateBoard.board_type` 기본값을 `Field(1)`로 바꿨다.
  - 요청 DTO 주석에 basic/schedule/proceedings mapping을 명시했다.
- `service.py`
  - 지원 board type에 basic을 추가했다.
  - basic board는 `schedule_board_detail`, `schedule_board_tasks`,
    `proceedings_board_detail`을 모두 금지한다.
- `router.py`
  - 함수명과 겹치던 지역 변수 `create_board`를 `created_board`로 고쳤다.
- `repository.py`
  - `#sqlmodel` 메모가 추가됐다.

이 작업에서 보이는 판단:

- 일반 게시글과 일정/회의록 게시글을 구분하려는 모델링 의도가 분명해졌다.
- detail이 없는 기본 글을 기본값 `board_type = 1`로 두려는 방향이다.
- 이전에 지적했던 router 변수명 충돌을 고친 점은 작은 품질 개선이다.
- repository 쪽 `#sqlmodel` 메모는 SQLModel을 검토 중이거나 SQLAlchemy 저장
  방식을 아직 고민 중이라는 신호로 보인다.

### 21:50 - `10c49c2 feat: add database session factory`

`backend/app/db/session.py`를 추가했다.

- `os.getenv("POSTGRES_DATABASE_URL")`로 DB URL을 읽는다.
- `create_engine(POSTGRES_DATABASE_URL)`으로 SQLAlchemy engine을 만든다.
- `sessionmaker(bind=engine, autoflush=False, autocommit=False)`로
  `SessionLocal`을 만든다.
- `get_session()` generator에서 `with SessionLocal() as session`으로 session을 열고 yield한다.

이 작업에서 보이는 판단:

- 이제 repository stub을 실제 DB insert로 바꾸기 위한 기반을 만들기 시작했다.
- FastAPI dependency로 쓸 수 있는 `get_session()` 형태를 떠올린 것으로 보인다.

### 22:05 - `daeb3c0 chore: clean up database session comments`

`session.py`의 주석을 정리했다.

- `# # Python code <-> SQLAlchemy engine <-> PostgreSQL`에서 중복 `#`를 제거했다.
- 파일 끝에 빈 줄이 추가됐다.

기능 변화는 작지만, 새로 만든 DB session 파일을 읽기 좋게 정리하려는 흐름이다.

## 무엇을 고려한 것으로 보이나

- API create 응답을 단순 성공 메시지가 아니라 실제 생성된 Board 형태로
  반환하려 한다.
- Router, Service, Repository의 계층 흐름을 유지하려 한다.
- 아직 DB 연결이 없다는 것을 알고 있고, repository에 `TODO: 실제 DB insert
  구현 후 생성된 BoardResponse를 반환`이라고 남겼다.
- 요청 DTO와 응답 DTO를 분리해야 한다는 감각이 생기고 있다.
- `board_type`은 단일 필드가 아니라 detail 필드들과 함께 검증되어야 한다는
  점을 고려하기 시작했다.
- 일정은 `start_at < end_at`이어야 한다는 시간 도메인 규칙을 고려했다.
- detail이 없는 일반 게시글을 따로 두기 위해 `basic board`를 추가했다.
- 함수명과 같은 지역 변수명을 피해야 한다는 코드 가독성 문제를 반영했다.
- 실제 DB 저장으로 가기 위해 engine/session factory가 먼저 필요하다는 점을
  고려하기 시작했다.

## 잘한 점

- `response_model=BoardResponse`를 붙여 FastAPI 응답 스키마가 명확해졌다.
- `return {"msg": ...}`에서 `BoardResponse` 반환으로 바뀐 것은 API 설계상
  좋은 방향이다.
- service가 repository를 호출하게 되어 계층 연결이 더 구체화됐다.
- `repository.py`가 비어 있던 상태에서 최소 함수가 생겼다.
- `TODO`로 실제 DB insert가 아직 남았음을 명시한 점은 좋다.
- `board_type`과 detail 조합 검증이 service 계층에 들어가면서 이전의 큰
  데이터 일관성 위험 하나가 줄었다.
- `SCHEDULE_BOARD_TYPE`, `PROCEEDINGS_BOARD_TYPE` 상수는 매직 넘버를 줄이는
  방향의 첫걸음이다.
- `start_at >= end_at`을 막은 것은 일정 도메인 규칙상 좋은 보강이다.
- `BASIC_BOARD_TYPE`을 추가해 detail이 없는 일반 Board를 표현할 수 있게 됐다.
- `created_board` 변수명 수정은 작지만 읽기 좋은 코드로 가는 개선이다.
- `get_session()`을 generator 형태로 만든 것은 FastAPI dependency로 연결하기 좋은 방향이다.

## 부족하거나 위험한 점

- repository는 아직 실제 DB 작업을 하지 않는다.
  - `id=1`은 고정값이다.
  - `created_at`, `updated_at`은 DB 값이 아니라 애플리케이션에서 임시 생성한 값이다.
  - insert, commit, rollback, refresh가 없다.
- `BoardResponse`에는 schedule/proceedings detail 응답 필드가 있지만,
  repository stub은 이 detail들을 채워주지 않는다.
- `ResponseScheduleBoardTaskDetail`에는 `board_id`가 없다.
  - task 응답에서 부모 detail/board와의 연결을 보여줄지 결정이 필요하다.
- `create_board` 변수명이 함수명과 같아 router 코드 가독성이 떨어진다.
  - 13:19 커밋에서 `created_board`로 고쳐졌다.
- `board_type`과 detail 조합 검증은 추가됐지만 아직 테스트가 없다.
- `board_type` 값이 1/2/3으로 바뀌었지만 DB check constraint나 enum은 아직 없다.
- `CreateBoard.board_type = Field(1)`은 기본값만 줄 뿐 허용 범위 검증은 아니다.
- `POSTGRES_DATABASE_URL`이 없으면 import 시점의 `create_engine(None)`에서
  바로 실패할 수 있다.
- PostgreSQL 드라이버가 requirements에 아직 보이지 않는다.
- `get_session()`은 생겼지만 router/service/repository 어디에도 아직 주입되지 않는다.
- service가 FastAPI `HTTPException`을 직접 발생시킨다.
  - 작은 학습 프로젝트에서는 괜찮지만, service를 프레임워크와 분리하려면
    도메인 예외를 던지고 router에서 HTTP로 변환하는 편이 낫다.
- 검증 실패가 모두 `400`으로 처리된다. 확정 기준상 body validation 실패는
  `422`로 통일하는 편이 맞다.
- `user_id`는 JWT 전 임시 필드이므로 실제 인증이 들어오면 제거해야 한다.

## 어떻게 개선하면 좋은가

1. DB session dependency를 실제 route/repository 흐름에 연결한다.
   - `get_session()`을 FastAPI `Depends`로 주입한다.
   - repository 함수가 `Session`을 인자로 받게 한다.
2. repository stub을 실제 DB insert로 바꾼다.
   - `Board`를 insert한다.
   - board type에 따라 detail table을 insert한다.
   - assignee/participant/carbon copy 연결 row를 insert한다.
   - commit 후 refresh한 값을 `BoardResponse`로 변환한다.
3. `POSTGRES_DATABASE_URL`과 DB driver 기준을 확인한다.
   - `.env.example` 또는 README에 환경변수명을 적는다.
   - PostgreSQL driver를 requirements에 추가한다.
4. 검증 테스트를 추가한다.
   - invalid `board_type`
   - basic board에 detail/task가 들어오는 경우
   - schedule detail 누락
   - proceedings detail 누락
   - schedule/proceedings detail 혼합
   - `start_at >= end_at`
5. service 예외 처리 기준을 정한다.
   - service에서 `HTTPException`을 직접 던질지
   - 도메인 예외를 던지고 router에서 HTTP 응답으로 바꿀지 결정한다.
   - 세부 기준은 [Board API 검증 실패 상태 코드 기준](./board-api-validation-status-policy.md)을 따른다.
6. 응답 변환 기준을 정한다.
   - repository가 ORM 객체를 반환하고 service가 DTO로 변환할지,
   - repository가 바로 `BoardResponse`를 반환할지 결정한다.
7. API 응답 테스트를 추가한다.
   - create 성공 시 `201`과 `BoardResponse`가 반환되는지 확인
   - repository 실패 시 500 또는 도메인 예외가 처리되는지 확인

## 사용자가 지금 도울 수 있는 말

- "이번 변화는 좋아. 이제 성공 응답 모양이 생겼으니 다음은 진짜 DB insert다."
- "`repository.insert_board()`의 `id=1` 고정값을 실제 insert/commit/refresh로
  바꾸자."
- "`BoardResponse`를 repository에서 만들지 service에서 만들지 역할을 정하자."
- "`board_type` 검증을 넣은 건 좋아. 이제 그 검증들이 깨지지 않게 테스트로
  고정하자."
- "`basic=1, schedule=2, proceedings=3` mapping을 enum이나 공통 상수로
  고정하자."
- "`get_session()`은 생겼으니 이제 router에서 `Depends(get_session)`로 받고,
  repository까지 `Session`을 넘기자."
- "`POSTGRES_DATABASE_URL` 없을 때 앱이 import 단계에서 터지지 않는지도 확인하자."
- "`HTTPException`을 service에서 직접 던질지, router에서 변환할지 팀 기준을
  정하자."
- "`400`과 `422`는 섞지 말고, body validation 실패는 422로 통일하자."

## RAG/Agent/MCP 관점

이번 커밋은 AI 계층과 직접 연결되지는 않는다. 하지만 요청/응답 DTO를
분리하기 시작한 것은 나중에 Agent가 API를 호출하거나 MCP tool schema를
만들 때 도움이 된다. Agent/MCP가 안정적으로 동작하려면 API 입력과 출력
스키마가 명확해야 하기 때문이다.

다만 AI 실행 기록, RAG 검색 결과, MCP tool call 로그는 여전히 Board에 직접
넣지 않는 편이 좋다. Board 생성 API가 안정화된 뒤 별도 `AgentRun`,
`ToolCall`, `Document`, `Chunk`, `RetrievalLog` 계층으로 확장하는 방향을
유지한다.
