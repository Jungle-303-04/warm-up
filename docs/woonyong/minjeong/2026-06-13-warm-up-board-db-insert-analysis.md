# 2026-06-13 warm-up Board DB 저장 흐름 분석

## 범위

- 사람: [민정](./README.md)
- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`minjeong`](https://github.com/Jungle-303-04/warm-up/tree/minjeong)
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: [`8368026`](https://github.com/Jungle-303-04/warm-up/commit/8368026c3616ba0200099b3791fa404084fe1b89)
- 커밋 메시지: `fix: schedule tasks only for schedule boards`
- 확인 시각: `2026-06-13 18:01:05 +09:00`
- 시각 자료: [Board 클래스 UML](./class-uml.md)

## 하루 요약

민정은 오전에는 `repository.insert_board()`의 고정 `BoardResponse(id=1, ...)`
stub을 실제 SQLAlchemy insert 흐름으로 바꿨고, 오후에는 Board API를 create
단일 기능에서 CRUD, 검색, pagination 구조로 확장했다.

이제 `POST /board/` 외에 `GET /board/`, `GET /board/{board_id}`,
`PUT /board/{board_id}`, `DELETE /board/{board_id}`가 생겼다. repository에는
검색 조건 조립, 전체 개수 조회, page/size pagination, 단건 조회, 수정, 삭제,
ORM -> DTO 변환 함수가 추가됐다. 마지막 커밋에서는 schedule task 응답이
schedule board에서만 채워지도록 보정했다.

## 시간대별 작업 흐름

### 01:47 - `617811b feat: implement board create repository flow`

변경 파일:

- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/service.py`
- `backend/app/domains/user/model.py`

구현 내용:

- `router.py`
  - `Depends(get_session)`으로 DB session을 주입받는다.
  - `service.create_board(db, request)`로 session을 전달한다.
- `service.py`
  - `create_board(db: Session, request: CreateBoard)`로 시그니처를 바꿨다.
  - 검증 후 `repository.insert_board(db, request)`를 호출한다.
- `repository.py`
  - `Board` ORM 객체를 생성하고 `db.add(board)` 후 `db.flush()`로 `board.id`를 확보한다.
  - schedule detail, proceedings detail, schedule task를 요청에 따라 생성한다.
  - assignee, participant, carbon copy 연결 row를 추가한다.
  - `BoardResponse`를 ORM 객체와 요청 DTO 값으로 조립한다.
  - 성공 시 `db.commit()`, 실패 시 `db.rollback()` 후 예외를 다시 던진다.
- `user/model.py`
  - `User(Base, IdMixin)` 모델을 추가했다.

### 02:08 - `2c3fa4d feat: initialize database on app startup`

변경 파일:

- `backend/app/main.py`
- `backend/requirements.txt`

구현 내용:

- `main.py`
  - `asynccontextmanager` 기반 lifespan을 추가했다.
  - 앱 시작 시 `Base.metadata.create_all(bind=engine)`을 호출한다.
  - 테스트용 `User(id=1)`이 없으면 생성한다.
- `requirements.txt`
  - `psycopg[binary]`를 추가했다.

### 02:10 - `6acd9f7 fix: initialize schedule tasks response data`

변경 파일:

- `backend/app/domains/board/repository.py`

구현 내용:

- schedule detail이 없는 요청에서도 `schedule_tasks` 변수가 참조될 수 있는
  문제를 막기 위해 기본값 `schedule_tasks = []`를 추가했다.

### 15:55 - `c6b0e08 feat: add board CRUD with search pagination`

변경 파일:

- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/schema.py`
- `backend/app/domains/board/service.py`
- `backend/requirements.txt`

구현 내용:

- `router.py`
  - `GET /board/` 목록 조회 endpoint를 추가했다.
  - `GET /board/{board_id}` 단건 조회 endpoint를 추가했다.
  - `PUT /board/{board_id}` 수정 endpoint를 추가했다.
  - `DELETE /board/{board_id}` 삭제 endpoint를 추가했다.
- `schema.py`
  - `UpdateBoard(CreateBoard)`를 추가했다.
  - `BoardSearchParams`를 추가해 `title`, `user_id`, `tag`, `page`, `size`를 받는다.
  - `BoardPageResponse`를 추가해 `items`, `total`, `page`, `size`를 반환한다.
- `service.py`
  - create/update 공통 검증을 `validate_board_request()`로 분리했다.
  - read/update/delete에서 board가 없으면 `404`를 반환한다.
- `repository.py`
  - `convert_to_board_response()`로 ORM row를 응답 DTO로 변환한다.
  - `select_boards()`에서 검색 조건과 pagination을 처리한다.
  - `select_board()`, `update_board()`, `delete_board()`를 추가했다.
  - detail row와 related user mapping row 삭제/추가 helper를 만들었다.
- `requirements.txt`
  - `psycopg[binary]` 표기를 `psycopg`, `psycopg-binary` 고정 버전으로 풀었다.

### 18:01 - `8368026 fix: schedule tasks only for schedule boards`

변경 파일:

- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/schema.py`

구현 내용:

- `convert_to_board_response()`에서 schedule detail이 있을 때만 schedule task를 조회한다.
- `insert_board()`에서도 schedule detail 생성 블록 안에서만 task id를 응답 DTO로 변환한다.
- `BoardResponse.schedule_board_tasks`를 `list[...] | None`으로 바꿨다.
- 의도는 basic/proceedings board 응답에서 schedule task가 빈 리스트로 보이는 것을 피하고,
  schedule board에만 task 응답을 붙이려는 것으로 보인다.

## 무엇을 고려한 것으로 보이나

- 이전에 만든 `get_session()`을 FastAPI dependency로 실제 연결하려 했다.
- DB 저장은 한 번에 끝내기보다 `flush()`로 id를 확보하고, 그 id로 detail/role
  row를 만드는 순서를 고려했다.
- 외래키 `user.id` 문제를 임시 `User` 모델과 `User(id=1)` seed로 해결하려 했다.
- schedule task response에는 DB에서 생성된 task id가 필요하다는 점을 고려했다.
- `psycopg[binary]`를 추가해 PostgreSQL 연결 의존성 문제를 인식했다.
- create만으로는 API 사용 흐름이 부족하므로 list/detail/update/delete까지 한 번에 확장했다.
- 검색은 우선 `title`, `user_id`, `tag`로 제한하고, page/size로 응답 크기를 제어하려 했다.
- 삭제/수정 시 child/detail/mapping row를 먼저 정리해야 FK 충돌을 피할 수 있다는 점을 고려했다.
- schedule task는 모든 board의 공통 필드가 아니라 schedule board 전용 detail이라는 점을 다시 반영했다.

## 잘한 점

- 가장 큰 막힘이던 repository stub을 실제 insert 흐름으로 바꿨다.
- Router -> Service -> Repository -> Model 흐름이 처음으로 끝까지 연결됐다.
- `db.flush()`로 commit 전 PK를 확보하는 판단은 좋다.
- 실패 시 `rollback()`을 호출하는 기본 트랜잭션 안전장치를 넣었다.
- 임시라도 `User` 모델을 만들어 `ForeignKey("user.id")` 문제를 풀었다.
- `schedule_tasks = []` 초기화 버그를 바로 고친 점이 좋다.
- create 이후 바로 CRUD 전체 형태로 확장해 API 표면을 빠르게 완성했다.
- `BoardSearchParams`와 `BoardPageResponse`를 추가해 목록 조회 계약을 명확히 했다.
- `validate_board_request()`로 create/update 공통 검증을 분리한 점은 중복을 줄이는 방향이다.
- not found 상황을 `404`로 처리한 점은 HTTP 의미에 맞다.
- schedule task 응답을 schedule board 전용으로 제한한 수정은 도메인 모델을 더 정확히 반영한다.

## 부족하거나 위험한 점

- `Base.metadata.create_all()`은 학습용으로는 좋지만 운영에서는 migration 도구가 필요하다.
- 앱 시작 시 `User(id=1)`을 자동 생성하는 방식은 테스트용 임시 처리다.
- `POSTGRES_DATABASE_URL`이 없으면 앱 import/startup 단계에서 실패할 수 있다.
- repository가 ORM 저장과 response DTO 조립을 동시에 맡아 책임이 커졌다.
- `service.py`는 여전히 FastAPI `HTTPException`을 직접 던진다.
- body validation 실패가 여전히 `400`이다. 기준상 `422`가 더 적절하다.
- `BoardType` enum이나 공통 상수 모듈이 없어 type 값이 여러 파일에 흩어져 있다.
- 테스트가 아직 없다. 이번 변화는 DB 저장까지 닿으므로 테스트 필요성이 더 커졌다.
- CRUD가 한 번에 커지면서 repository가 조회, 검색, 수정, 삭제, DTO 변환을 모두 맡게 됐다.
- `convert_to_board_response()`는 board마다 detail/user mapping을 별도 query로 조회하므로 목록 조회에서 N+1 query 위험이 있다.
- `UpdateBoard(CreateBoard)`는 수정 요청에서도 모든 생성 필드를 요구한다. 부분 수정이 아니라 전체 교체라는 정책을 명시해야 한다.
- update는 detail과 related user를 삭제 후 재삽입한다. 단순하지만 변경 이력이나 부분 변경 관점에서는 비용이 크다.
- `DELETE /board/{board_id}`는 204 응답이므로 body를 반환하지 않아야 한다. 현재 함수는 반환값이 없어서 방향은 맞지만 테스트로 고정해야 한다.
- `schedule_board_tasks`가 `None`으로 바뀌면서 클라이언트가 항상 list를 기대하던 경우 호환 문제가 생길 수 있다.

## 어떻게 개선하면 좋은가

1. 최소 통합 테스트를 추가한다.
   - basic board 생성
   - schedule board + task 생성
   - proceedings board 생성
   - 목록 조회 page/size
   - 단건 조회 404
   - update 후 detail/mapping 교체
   - delete 후 재조회 404
   - 잘못된 detail 조합
2. DB 설정을 명시한다.
   - `.env.example`
   - `POSTGRES_DATABASE_URL`
   - Docker compose와 실제 env 이름 일치 여부
3. migration 기준을 정한다.
   - 지금은 `create_all()`로 충분하지만, 이후 Alembic 같은 migration 도구가 필요하다.
4. 책임을 분리한다.
   - repository는 ORM 저장과 조회
   - service는 트랜잭션 흐름과 DTO 변환
   - schema는 body validation
5. `BoardType` enum 또는 공통 constants 모듈을 만든다.
6. 목록 조회 성능 기준을 정한다.
   - 지금 구조는 이해하기 쉽지만 N+1 query 위험이 있다.
   - SQLAlchemy `relationship()` 또는 bulk 조회 전략을 검토한다.
7. update 정책을 명시한다.
   - `PUT` 전체 교체인지, `PATCH` 부분 수정도 둘지 결정한다.

## 사용자가 지금 도울 수 있는 말

- "이제 진짜 DB insert까지 연결한 건 큰 진전이야."
- "`create_all()`과 `User(id=1)`은 학습용 임시 처리라고 표시하고, 다음에는 migration과 auth 기준을 정하자."
- "CRUD까지 한 번에 넓힌 건 좋지만, 이제는 테스트 없이는 위험해. create/list/detail/update/delete 최소 테스트를 먼저 고정하자."
- "repository가 너무 많은 일을 하기 시작했으니 다음엔 DTO 변환 위치와 query 전략을 정하자."
- "schedule task를 schedule board 전용으로 제한한 건 맞는 방향이지만, `None`과 빈 리스트 중 API 응답 정책을 팀에서 정하자."

## RAG/Agent/MCP 관점

이번 변화는 AI 계층과 직접 관련되지는 않지만 중요하다. Agent나 MCP tool이
Board 생성 API를 호출하려면 실제 DB에 저장되는 create flow와 조회/update/delete
계약이 안정화되어야 한다. 지금은 Agent가 호출할 수 있는 API 표면이 넓어진
상태지만, 테스트와 응답 정책이 아직 약하다. 다음 단계는 API contract와 테스트를
고정해 Agent나 MCP tool이 호출해도 깨지지 않는 입력/출력 규칙을 만드는 것이다.
