# 2026-06-11 warm-up Board 모델 분석

## 범위

- 사람: [민정](./README.md)
- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`minjeong`](https://github.com/Jungle-303-04/warm-up/tree/minjeong)
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: [`09b3578`](https://github.com/Jungle-303-04/warm-up/commit/09b357825dd02c758c80c5f16b37616dfb11415b)
- 커밋 메시지: `chore: update backend requirements`
- 확인 시각: `2026-06-11 11:01:46 +09:00`
- 시각 자료: [Board 클래스 UML](./class-uml.md)

## 하루 요약

민정은 `board` 도메인을 주석 기반 스캐폴드에서 실제 SQLAlchemy 테이블
모델링 단계로 끌어올렸다. API를 먼저 만들기보다 Board 하위 유형, 일정
task, 사용자 역할 관계를 먼저 모델링하려는 흐름이 보인다.

최신 커밋에서는 백엔드 의존성을 갱신하면서 `SQLAlchemy`를 추가했다. 이전
상태에서는 모델 코드는 SQLAlchemy를 import하지만 requirements에는 없었기
때문에, 이 커밋은 실행 환경의 명백한 막힘 하나를 줄인 작업이다.

## 전날 배경

### 2026-06-10 23:10 - `c681267 feat: add SQLAlchemy base mixins`

- `backend/app/db/base.py`를 추가했다.
- SQLAlchemy `DeclarativeBase` 기반의 `Base`를 만들었다.
- `created_at`, `updated_at`을 가진 `TimestampMixin`을 만들었다.
- autoincrement integer primary key를 제공하는 `IdMixin`을 만들었다.
- 사용하지 않는 `UserInfo` 주석 스텁을 남겼고, 이 부분은 이후 정리됐다.

이 커밋은 단순 FastAPI 스캐폴드에서 DB 기반 도메인 모델링으로 넘어가는
분기점이다.

## 시간대별 작업 흐름

### 03:49 - `1c202b5 feat: define board SQLAlchemy models`

Board 도메인의 첫 SQLAlchemy 모델 묶음을 구현했다.

- `Board`
  - `board_type`
  - `title`
  - `content`
  - optional `tag`
  - `user_id` foreign key to `user.id`
- `ScheduleBoardDetail`
  - `board_id`를 primary key로 쓰는 Board별 1개 상세 row 구조
  - `start_at`, `end_at`, `importance`
  - `importance`를 1부터 10까지로 제한하는 DB check constraint
- `ProceedingsBoardDetail`
  - `board_id`를 primary key로 쓰는 Board별 1개 상세 row 구조
  - `meeting_date`
- `BoardCarbonCopy`, `BoardAssignee`, `BoardParticipant`
  - `(board_id, user_id)` 복합 기본키를 가진 역할별 연결 테이블

이 작업에서 보이는 판단:

- 하나의 큰 Board 테이블에 모든 필드를 넣기보다, 공통 Board와 유형별 상세
  테이블을 나누려 했다.
- 참조인, 담당자, 참여자를 각각 연결 테이블로 분리해 여러 사용자가 하나의
  Board에 다양한 역할로 붙을 수 있게 했다.
- `importance` 같은 값은 애플리케이션 코드뿐 아니라 DB 제약으로도 막으려
  했다.

### 04:11 - `0f5fd69 feat: add schedule board task model`

`ScheduleBoardTask`를 추가했다.

- `IdMixin` 기반의 `id`
- `board_id` foreign key to `board.id`
- `task_name`
- `task_status`
- `task_status`를 1부터 4까지로 제한하는 check constraint

이 작업에서 보이는 판단:

- 일정 Board를 단순 기간 정보로만 보지 않고, 여러 개의 실행 task를 가질 수
  있는 대상으로 보고 있다.
- 코드 주석은 task 상태 값을 `Todo`, `In_progress`, `Done`, `Blocked`로
  해석한다.
- 워크플로우 상태를 DB 모델 안에서 표현하려는 시도가 시작됐다.

### 04:12 - `bc58a39 chore: remove unused user info stub`

`backend/app/db/base.py`에서 사용하지 않는 `UserInfo` 주석 스텁을 제거했다.

이 작업에서 보이는 판단:

- 실험 흔적이나 죽은 주석을 빠르게 정리했다.
- `base.py`를 사용자 모델 초안이 아니라 공통 ORM 기반 파일로 유지하려 했다.

### 11:01 - `09b3578 chore: update backend requirements`

기존의 매우 짧은 backend requirements를 고정 버전 목록으로 바꿨다. 주요
추가 항목은 다음과 같다.

- `fastapi==0.136.3`
- `SQLAlchemy==2.0.50`
- `pydantic==2.13.4`
- `python-dotenv==1.2.2`
- `uvicorn==0.49.0`
- `httptools`, `uvloop`, `watchfiles`, `websockets` 같은 서버 실행 보조 패키지

해결된 점:

- SQLAlchemy 모델 코드와 requirements 사이의 불일치가 줄었다.
- 이전의 `fastapi`, `uvicorn` 두 줄짜리 파일보다 환경 재현성이 좋아졌다.

남은 우려:

- PostgreSQL을 쓸 계획이라면 `psycopg`, `psycopg2`, `asyncpg` 같은 DB
  드라이버가 아직 없다.
- 현재 requirements는 사람이 직접 고른 최소 목록이라기보다 freeze 결과에
  가까워 보인다. 단기적으로는 괜찮지만, 나중에 의존성 의도를 검토하기
  어려울 수 있다.

## 무엇을 구현했나

- SQLAlchemy declarative base와 공통 mixin
- title/content/tag/user ownership 필드를 가진 `Board` 테이블
- 일정 시간 범위와 중요도 제약을 가진 `ScheduleBoardDetail`
- task 상태 제약을 가진 `ScheduleBoardTask`
- 회의일을 가진 `ProceedingsBoardDetail`
- 세 가지 Board-User 역할 연결 테이블
  - 참조인
  - 담당자
  - 참여자
- SQLAlchemy를 포함한 고정 버전 backend requirements

## 무엇을 고려한 것으로 보이나

- Board에는 여러 도메인 유형이 있고, 현재는 `board_type` 정수 값으로
  구분하려 한다.
- 일정 Board에는 모든 Board에 공통으로 넣기 어려운 특수 필드가 있다.
- 회의록 Board에는 별도의 회의일이 필요하다.
- 사용자는 Board와 여러 역할로 연결될 수 있으므로 역할별 연결 테이블을
  선택했다.
- `importance`, `task_status`처럼 범위가 정해진 값은 DB 제약으로도 보호하려
  했다.
- 여러 모델에서 반복될 `id`, `created_at`, `updated_at`은 mixin으로
  중앙화하려 했다.

## 잘한 점

- 구현 순서가 나쁘지 않다. 공통 ORM 기반, 도메인 모델, task 모델, 정리,
  의존성 보강 순서로 전진했다.
- SQLAlchemy 2 스타일의 `Mapped`, `mapped_column`을 사용한 점이 좋다.
- `IdMixin`, `TimestampMixin`은 모델이 늘어날 때 반복을 줄여준다.
- Board-User 역할 연결 테이블에 복합 기본키를 둔 것은 중복 역할 배정을
  막는 데 적절하다.
- 사용하지 않는 주석 스텁을 제거한 것은 작지만 좋은 정리다.
- `SQLAlchemy`를 requirements에 추가해 모델 코드와 실행 환경 사이의 간극을
  줄였다.

## 부족하거나 위험한 점

- `backend/app/main.py`는 `backend/app/domains/board/router.py`에서 `router`를
  import하지만, `router.py`에는 아직 `APIRouter` 인스턴스가 없다. 이 상태면
  모델 로직을 쓰기 전에 앱 import 단계에서 막힐 수 있다.
- `ForeignKey("user.id")`를 쓰지만 `origin/minjeong`에는 아직 `User` ORM
  모델이나 `user` 테이블 정의가 없다.
- SQLAlchemy `relationship()`이 없어 Board, detail, task, 사용자 역할
  테이블 사이의 ORM 탐색 방향이 아직 수동이다.
- DB engine/session 모듈이 없다.
- Alembic 같은 migration 경로가 없다.
- `board_type`, `task_status`가 정수 매직 넘버다. enum 또는 상수 이름이
  필요하다.
- 일정 모델에는 `importance` 범위 제약은 있지만 `end_at >= start_at` 제약은
  없다.
- timestamp가 timezone-naive `datetime.utcnow`를 사용한다.
- DTO, service, repository는 아직 주석/placeholder 단계다.

## 정규화와 RAG/Agent/MCP 확장 관점

현재 모델은 일반 협업 Board의 시작점으로는 꽤 괜찮다. `Board`를 중심에
두고, 일정 상세와 회의록 상세를 나누고, 담당자/참여자/참조인을 연결
테이블로 뺀 방향은 정규화 관점에서 좋은 출발이다. `ScheduleBoardTask`를
별도 테이블로 둔 것도 맞다. 일정 게시글 하나에 여러 task가 붙을 수 있기
때문이다.

다만 이 구조를 "정규화가 끝난 모델"로 보면 안 된다. 아직은 도메인 개념을
테이블로 나누기 시작한 초안이다.

가장 큰 위험은 `board_type`과 상세 테이블 사이의 일관성이다. 예를 들어
`board_type = 1`이면 일정 Board라는 뜻으로 보이지만, DB는 그 Board에
`ProceedingsBoardDetail`이 붙는 것을 막지 못한다. 반대로 `board_type = 2`인
Board에 `ScheduleBoardDetail`이 붙는 것도 현재 구조만으로는 막기 어렵다.
즉, "타입은 정수로 말하고 실제 상세 row는 별도 테이블에 존재하는" 구조라서
데이터 불일치가 생길 수 있다.

RAG, Agent, MCP까지 연결할 계획이라면 AI 관련 데이터를 `Board`에 직접
넣으면 안 된다. `Board`는 사람이 보는 작업, 게시글, 회의록, 일정의 중심
객체로 남기고, AI 실행과 검색 데이터는 별도 테이블로 분리해 Board나
Project를 참조하게 만드는 편이 낫다.

나중에 필요해질 수 있는 AI 계층 모델은 다음과 같다.

- `Document` 또는 `Source`
  - RAG에 넣을 원문, GitHub 문서, 회의록, 첨부파일, 코드 조각을 나타낸다.
- `Chunk`
  - 검색 단위로 쪼갠 텍스트를 나타낸다.
  - embedding model, chunk index, token count, source 위치가 필요하다.
- `RetrievalLog`
  - 어떤 질문에 어떤 chunk가 검색됐는지 기록한다.
  - score, rank, citation 정보를 남긴다.
- `AgentRun`
  - 에이전트가 어떤 목표로 실행됐는지 기록한다.
  - 특정 Board나 Project와 연결될 수 있다.
- `AgentStep` 또는 `ToolCall`
  - 에이전트의 단계별 판단, MCP tool 호출, GitHub 호출, 파일 읽기/쓰기,
    실행 결과를 기록한다.
- `McpServer`, `McpTool`
  - 어떤 MCP 서버와 tool을 썼는지, schema/version이 무엇인지 추적한다.
- `Approval` 또는 `Decision`
  - 에이전트 제안 중 사람이 승인한 결정과 그 맥락을 남긴다.

따라서 지금 단계의 결론은 분명하다. 민정이 만든 Board 모델은 일반 협업
보드의 중심 도메인으로는 괜찮다. 하지만 RAG/Agent/MCP를 포함하는 전체
데이터 모델로는 아직 부족하다. 지금은 AI 테이블을 억지로 붙이기보다
`Board`, `User`, `Project`, `BoardTask`, `BoardRole`을 먼저 안정화하고,
AI 실행 기록은 별도 계층으로 붙이는 방향이 좋다.

## 다음 개선 방향

1. 먼저 앱이 켜지는 상태를 만든다.
   - `backend/app/domains/board/router.py`에 `from fastapi import APIRouter`를 추가한다.
   - `router = APIRouter()`를 추가한다.
   - 임시 `GET /boards/` endpoint를 만들고 `[]`를 반환하게 한다.
2. 빠진 사용자 의존성을 결정한다.
   - 최소 `User` 모델을 구현할지 정한다.
   - 아니면 사용자 scope가 정해질 때까지 user foreign key를 임시 전략으로 처리한다.
3. DB 연결 인프라를 추가한다.
   - engine/session 구성을 만든다.
   - `.env.example`에 DB URL 기준을 적는다.
   - migration 전략을 정한다.
4. 매직 넘버를 없앤다.
   - `BoardType`, `TaskStatus` enum 또는 상수를 만든다.
   - DB check constraint와 코드 상수를 같은 의미로 맞춘다.
5. 테이블 구조가 안정되면 관계를 추가한다.
   - `Board.schedule_detail`
   - `Board.proceedings_detail`
   - `Board.tasks`
   - 역할 연결 테이블과 `User`의 relationship
6. 얇은 vertical slice 하나를 구현한다.
   - `BoardCreate`
   - `BoardRead`
   - repository create/list
   - service create/list
   - router create/list

## 막힘 신호

- 최소 API slice를 먼저 확정하기 전에 테이블 구조를 계속 확장하고 있을 수
  있다.
- User/auth ownership이 아직 정해지지 않았는데 여러 foreign key에 이미
  반영되어 있다.
- `router.py`에 exported `router`가 없어 백엔드가 import 단계에서 막힐 수
  있다.
- 모델은 생겼지만 persistence runtime path가 없다. 현재는 session dependency,
  migration, request/response schema, repository가 모두 비어 있다.

## 사용자가 지금 도울 수 있는 말

- "모델 방향은 좋아. 이제 테이블을 더 늘리기보다 먼저 가장 작은 board
  router로 서버가 켜지는 상태를 만들자."
- "`User`를 오늘 범위에 넣을지, 아니면 임시로 미룰지 먼저 정하자."
- "첫 API 목표는 `GET /boards/`가 `[]`를 반환하고, `POST /boards/`가 기본
  `Board`만 만드는 것으로 하자."
- "`board_type`, `task_status`는 service 로직이 붙기 전에 enum이나 상수로
  이름을 정해두자."
- "RAG/Agent/MCP 데이터는 Board에 직접 섞지 말고, 나중에 별도 실행/검색
  계층이 Board나 Project를 참조하게 하자."
- "router가 한 번 부팅되면 backend 실행 방법을 짧게 문서에 남기자."

## 현재 시각화 상태

현재 클래스 단위 구조는 [Board 클래스 UML](./class-uml.md)에 정리했다. 이
다이어그램은 미래의 router/service/repository 계획이 아니라, 현재 구현된
SQLAlchemy 클래스만 반영한다.
