# 민정 warm-up 커밋 진화 분석

## 분석 기준

- 저장소: `Jungle-303-04/warm-up`
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 범위: `c27ed3a Initial commit`부터 `842d495 fix: skip duplicate RAG index storage`까지
- 최신 확인 시각 기준: `2026-06-16 20:00:37 +09:00`

볼트의 `person-lee-minjeong.md` 기준에 따라 이 문서는 개발 작업만 다룬다.
창작 인물 자료나 말투 자료는 구현 분석의 근거로 섞지 않는다. 여기서 말하는
"의도"는 성격이나 개인 동기 추측이 아니라, 커밋 메시지, 코드, 주석, README에서
확인되는 구현 의도 또는 설계 방향을 뜻한다.

## 한 줄 흐름

민정의 브랜치는 `AI Board` 제품 구상에서 출발해 FastAPI/React/Docker 실행
골격, Board CRUD, SQLAlchemy 저장 흐름을 먼저 만든 뒤, GitHub OAuth, RAG
인덱싱, SQL/vector 저장, repository/branch/commit 범위의 RAG ask, LangGraph
답변 그래프, agent chat scaffold까지 확장해 온 흐름이다.

현재까지의 핵심 상태는 다음과 같다.

- 좋은 방향: 기획을 먼저 쪼개고, 일반 보드 CRUD 기반을 만든 뒤 AI/RAG 기능으로 넘어갔다.
- 좋은 방향: `api`, `service`, `domain`, `external`, `ports` 책임 분리를 시도하고 있다.
- 새 진전: GitHub repository를 commit 단위 evidence로 인덱싱하고, `/rag/ask`를 해당 evidence 범위로 제한했다.
- 아직 부족한 점: 테스트, env/secret 문서, SQL/vector 저장 일관성, 중복 인덱싱 race condition, agent 경계가 약하다.
- 지금 가장 중요한 다음 작업: RAG indexing과 `/rag/ask` 테스트, idempotency/unique constraint, `.env.example`, SQL/vector partial failure 기준을 고정하는 것.

## 전체 커밋 흐름

| 순서 | 커밋 | 시각 | 의미 |
|---:|---|---|---|
| 1 | `c27ed3a Initial commit` | 2026-06-05 16:57 | 저장소 시작 |
| 2 | `4aa5f95 Add planning docs for AI collaboration tool` | 2026-06-07 17:38 | 제품/AI/모듈 계획 문서화 |
| 3 | `c3f355b feat: scaffold FastAPI and React app with Docker services` | 2026-06-09 22:23 | 전체 실행 골격 구성 |
| 4 | `3d79dd0 feat: scaffold board domain structure` | 2026-06-10 11:07 | Board 도메인 계층 파일 생성 |
| 5 | `c681267 feat: add SQLAlchemy base mixins` | 2026-06-10 23:10 | SQLAlchemy 공통 기반 생성 |
| 6 | `1c202b5 feat: define board SQLAlchemy models` | 2026-06-11 03:49 | Board 중심 테이블 모델링 |
| 7 | `0f5fd69 feat: add schedule board task model` | 2026-06-11 04:11 | 일정 작업 모델 추가 |
| 8 | `bc58a39 chore: remove unused user info stub` | 2026-06-11 04:12 | 불필요한 스텁 제거 |
| 9 | `09b3578 chore: update backend requirements` | 2026-06-11 11:01 | 백엔드 의존성 고정 |
| 10 | `fd86323 feat: add board create DTO and route` | 2026-06-11 17:00 | 생성 요청 DTO와 route 생성 |
| 11 | `ba8ba00 feat: connect board create route to service` | 2026-06-11 20:30 | Router -> Service 연결 |
| 12 | `23297e5 chore: enable backend hot reload in Docker` | 2026-06-11 20:34 | 개발 피드백 루프 개선 |
| 13 | `905283a feat: add board create response flow` | 2026-06-12 01:21 | 응답 DTO와 Repository stub 연결 |
| 14 | `2a8476a feat: add board type validation in service` | 2026-06-12 11:27 | Board type/detail 조합 검증 추가 |
| 15 | `1e8a549 feat: support basic board type validation` | 2026-06-12 13:19 | Basic board type 추가 |
| 16 | `10c49c2 feat: add database session factory` | 2026-06-12 21:50 | SQLAlchemy session factory 추가 |
| 17 | `daeb3c0 chore: clean up database session comments` | 2026-06-12 22:05 | DB session 주석 정리 |
| 18 | `617811b feat: implement board create repository flow` | 2026-06-13 01:47 | 실제 Board insert 흐름 구현 |
| 19 | `2c3fa4d feat: initialize database on app startup` | 2026-06-13 02:08 | 앱 시작 시 DB table/user 초기화 |
| 20 | `6acd9f7 fix: initialize schedule tasks response data` | 2026-06-13 02:10 | schedule task 응답 초기화 버그 수정 |
| 21 | `c6b0e08 feat: add board CRUD with search pagination` | 2026-06-13 15:55 | Board CRUD/search/pagination 확장 |
| 22 | `8368026 fix: schedule tasks only for schedule boards` | 2026-06-13 18:01 | schedule task 응답 정책 보정 |
| 23 | `0d571f3 feat: scaffold RAG and GitHub domains` | 2026-06-14 16:32 | RAG/GitHub 도메인 확장 시작 |
| 24 | `723927e feat: add GitHub RAG indexing pipeline` | 2026-06-14 22:04 | GitHub 파일을 RAG chunk로 바꾸는 pipeline 추가 |
| 25 | `95cdb38 refactor: split RAG chunking modules` | 2026-06-14 22:26 | chunking 책임을 module로 분리 |
| 26 | `696c85f feat: wire RAG indexing services` | 2026-06-14 23:31 | DI container와 RAG router/service 조립 |
| 27 | `21b1961 docs: add source code comments` | 2026-06-14 23:38 | 주요 source comment 보강 |
| 28 | `a5c4b66 feat: store RAG indexes in SQL and vector DB` | 2026-06-15 01:04 | RAG SQL/vector 저장 구조 추가 |
| 29 | `6b59517 refactor: align layered pipeline and auth structure` | 2026-06-15 01:41 | auth와 ports/external 계층 정렬 |
| 30 | `53dfba1 feat: add github oauth test console` | 2026-06-15 01:55 | GitHub OAuth frontend 확인 화면 추가 |
| 31 | `ca6152c fix: localize oauth login screen` | 2026-06-15 02:00 | OAuth 화면 한글화 |
| 32 | `0574d07 feat: add repository RAG answer workflow` | 2026-06-15 02:42 | repository RAG 답변 흐름 추가 |
| 33 | `266b5c3 Refactor backend modules and add agent chat scaffold` | 2026-06-15 04:12 | top-level module 재배치와 agent scaffold 추가 |
| 34 | `6b07845 docs: add RAG study diagrams and notes` | 2026-06-15 21:17 | RAG 학습 문서와 다이어그램 추가 |
| 35 | `804d34f refactor: route RAG answer flow through LangGraph` | 2026-06-15 21:51 | RAG answer flow를 LangGraph로 이동 |
| 36 | `7b51bd9 docs: clarify RAG ask boundaries and run ids` | 2026-06-15 23:22 | `/rag/ask`, run_id, repo/branch/commit 경계 문서화 |
| 37 | `d0a73de feat: scope RAG ask by repository commit` | 2026-06-16 02:10 | RAG ask evidence를 repository/branch/commit으로 제한 |
| 38 | `1865d09 refactor: branch RAG answer graph on evidence` | 2026-06-16 03:13 | evidence 유무에 따른 LangGraph 분기 |
| 39 | `842d495 fix: skip duplicate RAG index storage` | 2026-06-16 04:13 | 같은 repo/branch/commit RAG index 재사용 |

## 커밋 단위 분석

### 1. `c27ed3a` - Initial commit

구현한 것:

- `README.md`에 저장소 시작점을 만들었다.

의도와 흐름:

- 아직 제품이나 기술 선택보다 저장소를 여는 단계다.

고려하지 못한 것:

- 프로젝트 목표, 실행 방법, 스택, 모듈 경계가 아직 없다.

개선 방향:

- 이후 커밋처럼 README에 제품 방향, 스택, 우선순위를 추가하는 방식이 맞다.

### 2. `4aa5f95` - AI collaboration tool 계획 문서

구현한 것:

- README를 크게 확장했다.
- `docs/auth.md`, `docs/projects.md`, `docs/posts-and-comments.md`, `docs/rag.md`,
  `docs/agent.md`, `docs/github-integration.md`, `docs/ai-writing-and-classification.md`
  등을 추가했다.
- React, FastAPI, PostgreSQL, JWT, GPT, RAG, GitHub MCP/API를 큰 구성요소로 잡았다.

의도와 흐름:

- 처음부터 AI 기능을 바로 구현하기보다, 제품을 모듈 단위로 쪼개려 했다.
- README의 "처음에는 프로젝트, 멤버 추가, 게시글 기능부터 만들고, AI 기능은
  단계적으로 붙인다"는 문장을 보면 MVP 우선순위를 의식한 것으로 보인다.
- RAG, Agent, MCP는 초기 필수 구현이 아니라 확장 기능으로 둔 판단이 좋다.

고려하지 못한 것:

- 각 모듈의 최소 API 계약이 아직 없다.
- 데이터 모델이 아직 ERD나 테이블 기준으로 내려오지 않았다.
- RAG/Agent/MCP 실행 기록을 어떤 테이블에 남길지까지는 정해지지 않았다.
- "프로젝트 멤버 단일 권한" 같은 MVP 가정은 좋지만, 나중에 권한 확장 시
  어떤 지점에서 바꿀지 기준이 없다.

개선 방향:

- README 계획을 `User`, `Project`, `Board/Post`, `Comment`, `Document`,
  `AgentRun`, `ToolCall`, `RetrievalLog` 같은 최소 엔티티 목록으로 한 단계
  더 내린다.
- RAG/Agent/MCP는 Board 테이블에 섞지 말고, 별도 실행/검색 로그 테이블이
  Board나 Project를 참조하게 설계한다.

### 3. `c3f355b` - FastAPI/React/Docker 스캐폴드

구현한 것:

- FastAPI root endpoint를 만들었다.
- Vite React 앱을 생성했다.
- Dockerfile과 `docker-compose.yml`에 app, postgres, redis 서비스를 두었다.
- `mise.toml`, `.gitignore`, frontend package 파일이 추가됐다.

의도와 흐름:

- 문서로만 있던 계획을 실행 가능한 full-stack 골격으로 옮기려 했다.
- PostgreSQL과 Redis를 compose에 먼저 둔 것은 장기적으로 DB와 비동기/캐시성
  작업을 생각한 것으로 보인다.

고려하지 못한 것:

- compose가 `.env`를 요구하지만 `.env.example`이 없다.
- PostgreSQL 서비스는 있지만 FastAPI DB 연결, session, migration은 없다.
- Redis는 아직 사용하는 코드가 없어 초기 복잡도를 조금 올린다.
- frontend는 Vite 기본 템플릿 상태라 제품 화면과 연결되지는 않는다.

개선 방향:

- `.env.example`을 추가한다.
- FastAPI에 DB URL 설정, engine/session dependency, health check를 붙인다.
- Redis는 실제 사용 시점까지 선택적 구성으로 두거나 사용 목적을 문서화한다.

### 4. `3d79dd0` - Board 도메인 계층 파일 생성

구현한 것:

- `backend/app/domains/board/` 아래에 `model.py`, `repository.py`, `router.py`,
  `schema.py`, `service.py`를 만들었다.
- `main.py`에서 board router를 include하려고 했다.

의도와 흐름:

- Java/Spring의 Controller-Service-Repository 감각을 FastAPI에 옮기려 했다.
- 주석을 보면 각 파일의 책임을 먼저 정리하고 들어가려는 흐름이 보인다.

고려하지 못한 것:

- 이 시점의 `main.py`는 `from app.domains.board.router import router as board_router`
  를 사용하지만 `router.py`에는 아직 `router` 객체가 없다.
- 즉 계층 파일은 생겼지만 앱 import가 깨질 수 있는 상태였다.

개선 방향:

- skeleton을 만들 때도 import 가능한 최소 객체를 같이 둔다.
- 예: `board = APIRouter(prefix="/boards")`를 먼저 만들고 `main.py`에서 같은
  이름을 import한다.

### 5. `c681267` - SQLAlchemy Base와 Mixin

구현한 것:

- `Base(DeclarativeBase)`를 만들었다.
- `TimestampMixin`, `IdMixin`을 만들었다.

의도와 흐름:

- 여러 모델에서 반복될 `id`, `created_at`, `updated_at`을 공통화하려 했다.
- SQLAlchemy 2.0 스타일의 `Mapped`, `mapped_column`을 사용했다.

고려하지 못한 것:

- `datetime.utcnow`는 timezone 정보가 없는 datetime을 만든다.
- `created_at`, `updated_at`을 애플리케이션 기본값으로 둘지 DB server default로
  둘지 기준이 없다.
- 주석 처리된 `UserInfo` 스텁이 남아 있어 모델 기준이 흐려졌다.

개선 방향:

- timezone-aware datetime 또는 DB server default 사용 여부를 팀 기준으로 정한다.
- `User`는 별도 도메인 모델로 만들고, base 파일은 공통 기반만 남긴다.

### 6. `1c202b5` - Board SQLAlchemy 모델 정의

구현한 것:

- `Board`, `ScheduleBoardDetail`, `ProceedingsBoardDetail`을 만들었다.
- `BoardCarbonCopy`, `BoardAssignee`, `BoardParticipant` 연결 테이블을 만들었다.
- `importance`에 `CheckConstraint`를 추가했다.

의도와 흐름:

- 하나의 Board를 기본 테이블로 두고, board type별 상세 정보를 별도 테이블로
  정규화하려 했다.
- 참조인/담당자/참여자를 별도 연결 테이블로 둔 것은 역할별 N:M 관계를
  표현하려는 시도다.

고려하지 못한 것:

- `ForeignKey("user.id")`가 있지만 `User` 모델은 아직 없다.
- `relationship()`이 없어 ORM 객체 간 탐색 방향이 정의되지 않았다.
- `board_type` 값과 실제 detail 테이블 사이의 일관성을 DB나 서비스에서 아직
  강제하지 않는다.
- migration, session, engine이 없어 모델이 실제 DB schema로 적용되지 않는다.

개선 방향:

- `User` 모델 또는 임시 user table 기준을 먼저 세운다.
- `Board`와 detail/role 모델 사이의 `relationship()`과 cascade 기준을 정한다.
- `board_type`은 enum 또는 상수로 의미를 고정한다.
- DB 제약만으로 어려운 "type별 detail 하나만 허용" 규칙은 DTO/service 검증과
  테스트로 보완한다.

### 7. `0f5fd69` - ScheduleBoardTask 모델 추가

구현한 것:

- `ScheduleBoardTask` 모델을 추가했다.
- `task_status`에 1부터 4까지의 `CheckConstraint`를 추가했다.

의도와 흐름:

- 일정 board가 단순 기간/중요도만 갖는 것이 아니라, 하위 task 목록을 가질 수
  있다고 본 것이다.
- `task_status` 범위를 DB에서 막으려는 판단은 좋다.

고려하지 못한 것:

- 최초 추가 시 task가 `board.id`를 직접 참조했다.
- 이후 `fd86323`에서 `schedule_board_detail.board_id`를 참조하도록 바뀌었는데,
  이 변화는 "task는 모든 board가 아니라 schedule detail에 속한다"는 방향으로
  더 정확해진 것이다.
- task 순서, 담당자, due date 같은 확장 필드는 아직 없다.

개선 방향:

- 현재처럼 schedule detail에 매달리는 방향이 더 자연스럽다.
- `task_status`도 enum으로 분리해 값 의미를 코드에서 읽히게 만든다.

### 8. `bc58a39` - 사용하지 않는 UserInfo 스텁 제거

구현한 것:

- `base.py`에 남아 있던 `UserInfo` 주석 스텁을 제거했다.

의도와 흐름:

- 공통 base 파일을 깨끗하게 만들려는 정리성 커밋이다.

고려하지 못한 것:

- `User` 스텁은 제거됐지만, `Board.user_id`와 role 연결 테이블은 여전히
  `user.id`를 참조한다.
- 즉 주석 스텁 제거는 맞지만 실제 User 모델 기준은 여전히 필요하다.

개선 방향:

- `User` 모델을 별도 auth/user 도메인에 정의하거나, JWT 전까지 임시 user
  fixture/table을 명시한다.

### 9. `09b3578` - backend requirements 갱신

구현한 것:

- `fastapi`, `uvicorn`만 있던 requirements를 고정 버전 목록으로 확장했다.
- `SQLAlchemy`, `pydantic`, `python-dotenv`, `watchfiles` 등이 들어갔다.

의도와 흐름:

- SQLAlchemy 모델 코드가 생긴 뒤 실행 환경에도 SQLAlchemy를 맞추려 했다.
- hot reload나 `.env` 사용 가능성을 고려한 흔적이 보인다.

고려하지 못한 것:

- PostgreSQL을 쓸 계획인데 PostgreSQL 드라이버가 아직 없다.
- requirements가 사람이 읽는 최소 의존성 목록이라기보다 freeze 결과에 가깝다.
- 왜 필요한 의존성인지 구분이 어렵다.

개선 방향:

- 학습 프로젝트에서는 `requirements.in` 또는 README에 "직접 의존성"과
  "잠금 결과"를 나눠 적으면 좋다.
- DB 연결 단계에서 `psycopg`, `psycopg2`, `asyncpg` 중 하나를 명확히 고른다.

### 10. `fd86323` - Board create DTO와 route

구현한 것:

- `CreateBoard`와 type별 nested detail DTO를 만들었다.
- `importance`, `task_status`에 Pydantic `Field` 범위 검증을 붙였다.
- `POST /board/` route를 만들었다.
- 이전 task FK를 `board.id`에서 `schedule_board_detail.board_id`로 고쳤다.

의도와 흐름:

- DB 모델을 API 요청 body 구조로 옮기려 했다.
- DB check constraint와 Pydantic validation을 맞추려 한 점이 좋다.
- route가 생기면서 `APIRouter` import 문제도 한 단계 해결됐다.

고려하지 못한 것:

- route는 아직 `{"msg": "success"}`만 반환한다.
- service/repository/DB insert가 아직 연결되지 않았다.
- `board_type`과 detail 조합 검증이 없다.
- JWT가 없어서 `user_id`를 body로 받는 임시 구조다.
- endpoint가 `/board/` singular인데 팀 API 규칙이 plural이면 `/boards/`로 맞춰야 한다.

개선 방향:

- request DTO 검증에 `model_validator`를 추가한다.
- `POST /boards/`처럼 자원명 규칙을 맞춘다.
- 성공 응답 DTO를 붙이고, 이후 실제 insert와 연결한다.

### 11. `ba8ba00` - Router에서 Service 호출

구현한 것:

- router가 `service.create_board()`를 호출하게 만들었다.
- 성공 시 `201`을 반환하게 했다.
- service는 일단 `return 1`을 반환한다.

의도와 흐름:

- route 안에서 모든 일을 처리하지 않고 service 계층으로 넘기려 했다.
- "생성 성공 여부"를 insert count 같은 값으로 판단하려 한 것으로 보인다.

고려하지 못한 것:

- service가 실제 repository나 DB를 호출하지 않는다.
- `insert_count < 1`은 실제 insert 결과가 없는 상태에서는 의미가 약하다.
- 성공 응답이 실제 생성된 리소스가 아니라 문자열 메시지다.

개선 방향:

- service가 repository를 호출하게 한다.
- 성공 시 생성된 Board response를 반환한다.
- 실패는 insert count보다 예외/트랜잭션 실패로 처리한다.

### 12. `23297e5` - Docker hot reload

구현한 것:

- compose의 app 서비스에 `./backend/app:/app/app` volume을 추가했다.
- `uvicorn app.main:app --reload` 명령을 넣었다.

의도와 흐름:

- 혼자 빠르게 고치고 바로 확인할 수 있는 개발 루프를 만들려 했다.
- 현재 민정이 AI 도움 없이 직접 구현을 익히는 상황에서는 좋은 피드백 장치다.

고려하지 못한 것:

- volume이 `backend/app`만 연결되므로 requirements나 Dockerfile 변경은 즉시 반영되지 않는다.
- reload는 개발용이고 운영용 command와 분리되어야 한다.

개선 방향:

- 개발 compose와 운영 compose를 나누거나 README에 개발용 설정임을 적는다.
- requirements 변경 시 rebuild가 필요하다는 점을 문서화한다.

### 13. `905283a` - Board create 응답 흐름

구현한 것:

- `BoardResponse`와 response detail DTO를 만들었다.
- route에 `response_model=BoardResponse`를 붙였다.
- service가 repository를 호출하게 했다.
- `repository.insert_board()` stub이 `BoardResponse(id=1, ...)`를 반환하게 했다.

의도와 흐름:

- 단순 성공 메시지에서 실제 API contract로 이동했다.
- Router -> Service -> Repository 흐름을 완성하는 방향으로 갔다.
- TODO 주석으로 실제 DB insert가 남아 있음을 인식하고 있다.

고려하지 못한 것:

- repository는 아직 DB insert를 하지 않는다.
- `id=1` 고정값과 애플리케이션 생성 UTC 시간이 실제 DB 상태를 대변하지 않는다.
- response DTO에는 detail 필드가 있지만 repository stub은 detail을 채우지 않는다.
- router 변수명이 `create_board`라 함수명과 겹친다.

개선 방향:

- DB session dependency를 만들고 repository에 주입한다.
- `Board`, detail, role 연결 row를 insert한 뒤 commit/refresh한다.
- ORM 객체를 DTO로 변환하는 책임을 service에 둘지 repository에 둘지 정한다.
- router 내부 변수명은 `created_board`로 바꾼다.

### 14. `2a8476a` - Board type validation in service

구현한 것:

- `SCHEDULE_BOARD_TYPE = 1`, `PROCEEDINGS_BOARD_TYPE = 2` 상수를 추가했다.
- 지원하지 않는 `board_type`을 막았다.
- schedule board와 proceedings board의 필수 detail과 금지 detail 조합을 검증했다.
- `start_at >= end_at`을 막았다.

의도와 흐름:

- 단순 타입 검증을 넘어 여러 필드의 조합 일관성을 지키려 했다.
- 이전까지 가장 큰 위험이던 "board_type과 detail이 서로 안 맞는 요청"을 줄였다.

고려하지 못한 것:

- 검증 실패가 모두 `400`이다. 현재 팀 기준으로는 body validation 실패는 `422`가 맞다.
- service가 FastAPI `HTTPException`을 직접 던져 프레임워크 결합이 생긴다.
- 동일 검증이 테스트로 고정되어 있지 않다.
- 상수는 service에만 있어 schema/model과 값 기준이 흩어질 수 있다.

개선 방향:

- body validation에 가까운 검증은 `schema.py`의 Pydantic `model_validator`로 옮긴다.
- 그러면 FastAPI가 기본적으로 `422`를 반환한다.
- DB 상태 조회가 필요한 비즈니스 규칙만 service에 남긴다.
- service에는 도메인 예외를 두고 router에서 HTTP status로 변환하는 방식을 검토한다.
- 검증 케이스를 테스트로 만든다.

### 15. `1e8a549` - Basic board type validation

구현한 것:

- `BASIC_BOARD_TYPE = 1`, `SCHEDULE_BOARD_TYPE = 2`, `PROCEEDINGS_BOARD_TYPE = 3`
  mapping을 `model.py`와 `service.py`에 추가했다.
- `CreateBoard.board_type`의 기본값을 `Field(1)`로 바꿨다.
- basic board에는 schedule/proceedings detail과 schedule task가 들어오지 못하게 했다.
- router 지역 변수명을 `create_board`에서 `created_board`로 바꿨다.
- repository에 `#sqlmodel` 메모를 남겼다.

의도와 흐름:

- detail이 없는 일반 게시글을 `basic board`로 표현하려는 의도다.
- schedule/proceedings board만 detail을 가져야 한다는 도메인 규칙이 더 선명해졌다.
- 이전 리뷰에서 지적했던 변수명 충돌을 바로 고친 점은 좋은 신호다.

고려하지 못한 것:

- `board_type` mapping이 `model.py`, `schema.py`, `service.py`에 흩어져 있다.
- `Field(1)`은 기본값을 줄 뿐 1/2/3 허용 범위를 보장하지 않는다.
- 여전히 검증 실패 status는 `400`이고, body validation 기준으로는 `422`가 더 적절하다.
- SQLModel을 쓸지 SQLAlchemy를 계속 쓸지 결정하지 않은 신호가 보인다.
- repository는 여전히 실제 DB insert 없이 stub이다.

개선 방향:

- `BoardType` enum 또는 공통 constants 모듈을 만든다.
- `CreateBoard`에 Pydantic `model_validator`를 넣어 basic/schedule/proceedings
  조합 검증을 `422`로 고정한다.
- SQLModel로 갈지 SQLAlchemy로 갈지 먼저 결정하고, 한 가지 패턴으로 repository를 구현한다.
- `basic`, `schedule`, `proceedings` 정상/실패 케이스를 테스트로 추가한다.

### 16. `10c49c2` - Database session factory

구현한 것:

- `backend/app/db/session.py`를 새로 만들었다.
- `POSTGRES_DATABASE_URL` 환경변수를 읽어 SQLAlchemy engine을 만든다.
- `SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)`를 정의했다.
- `get_session()` generator를 만들어 session을 열고 yield한다.

의도와 흐름:

- repository stub을 실제 DB insert로 바꾸기 전에 DB session dependency를 준비하려는 흐름이다.
- FastAPI에서 `Depends(get_session)`로 주입할 수 있는 모양을 떠올린 것으로 보인다.

고려하지 못한 것:

- `POSTGRES_DATABASE_URL`이 없으면 import 시점에 `create_engine(None)`이 실패할 수 있다.
- PostgreSQL driver 의존성이 아직 명확하지 않다.
- `get_session()`이 router/service/repository에 아직 연결되지 않았다.
- transaction commit/rollback 책임을 어디에 둘지 정해지지 않았다.

개선 방향:

- `.env.example` 또는 README에 `POSTGRES_DATABASE_URL`을 명시한다.
- PostgreSQL driver를 requirements에 추가한다.
- route에서 `Depends(get_session)`로 `Session`을 받고 repository까지 전달한다.
- repository에서 insert/commit/refresh 흐름을 구현한다.

### 17. `daeb3c0` - Database session comments cleanup

구현한 것:

- `session.py`의 중복 `#` 주석을 정리했다.
- 파일 끝에 빈 줄을 추가했다.

의도와 흐름:

- 새로 만든 DB session 파일을 읽기 좋게 정리하려는 작은 chore다.

고려하지 못한 것:

- 기능 변화는 없다.
- 파일 끝 빈 줄에 공백이 남아 있을 수 있어 formatter로 정리하는 편이 좋다.

개선 방향:

- `ruff format` 또는 팀 formatter를 적용한다.
- 다음 커밋은 주석 정리보다 session을 실제 API 흐름에 연결하는 쪽이 더 중요하다.

### 18. `617811b` - Board create repository flow

구현한 것:

- router가 `Depends(get_session)`으로 DB session을 받는다.
- service가 `Session`과 `CreateBoard`를 함께 받아 repository에 넘긴다.
- repository가 `Board`, type별 detail, schedule task, 역할 연결 row를 ORM 객체로 생성한다.
- `db.flush()`로 `board.id`와 task id를 확보하고 `BoardResponse`를 조립한다.
- 성공 시 `db.commit()`, 실패 시 `db.rollback()`을 수행한다.
- 임시 `User` 모델을 추가했다.

의도와 흐름:

- 이전까지의 `id=1` stub을 실제 DB insert 흐름으로 바꾸려는 핵심 진전이다.
- 외래키 문제를 풀기 위해 최소 User 모델을 먼저 만든 것으로 보인다.

고려하지 못한 것:

- repository가 저장과 response DTO 조립을 모두 맡아 책임이 커졌다.
- 관계형 저장 로직이 커졌지만 테스트가 없다.
- `service.py`의 HTTP 예외와 `400` status 기준은 여전히 남아 있다.

개선 방향:

- basic/schedule/proceedings create 통합 테스트를 추가한다.
- DTO 변환 책임을 service 또는 mapper 함수로 분리할지 정한다.
- transaction 책임을 repository에 둘지 service에 둘지 팀 기준을 잡는다.

### 19. `2c3fa4d` - App startup DB initialization

구현한 것:

- FastAPI lifespan에서 `Base.metadata.create_all(bind=engine)`을 호출한다.
- 앱 시작 시 `User(id=1)`이 없으면 생성한다.
- `psycopg[binary]`를 requirements에 추가했다.

의도와 흐름:

- 로컬에서 바로 board create를 테스트할 수 있게 테이블과 임시 user를 준비하려는 흐름이다.

고려하지 못한 것:

- `create_all()`은 migration을 대체하기 어렵다.
- `User(id=1)` 자동 생성은 테스트용 임시 처리다.
- `POSTGRES_DATABASE_URL`이 없을 때의 실패 메시지나 fallback이 없다.

개선 방향:

- 학습 단계에서는 유지하되 임시 처리임을 문서화한다.
- 이후 Alembic 같은 migration 도구로 옮긴다.
- `.env.example`에 DB URL을 명시한다.

### 20. `6acd9f7` - Schedule task response initialization

구현한 것:

- schedule detail이 없는 요청에서도 `schedule_tasks` 변수가 참조되지 않도록
  `schedule_tasks = []`를 기본값으로 초기화했다.

의도와 흐름:

- 실제 insert 흐름을 만들면서 발견한 런타임 위험을 빠르게 고친 커밋이다.

고려하지 못한 것:

- 이런 버그는 테스트가 있었다면 더 빨리 잡혔을 가능성이 크다.

개선 방향:

- basic board 생성 테스트를 추가해 schedule task가 없는 경우도 고정한다.

### 21. `c6b0e08` - Board CRUD with search pagination

구현한 것:

- `GET /board/` 목록 조회 endpoint를 추가했다.
- `GET /board/{board_id}` 단건 조회 endpoint를 추가했다.
- `PUT /board/{board_id}` 수정 endpoint를 추가했다.
- `DELETE /board/{board_id}` 삭제 endpoint를 추가했다.
- `BoardSearchParams`, `BoardPageResponse`, `UpdateBoard` DTO를 추가했다.
- repository에 `convert_to_board_response()`, `select_boards()`, `select_board()`,
  `update_board()`, `delete_board()`를 추가했다.
- detail row와 관련 user mapping row를 삭제/추가하는 helper를 만들었다.

의도와 흐름:

- create 하나에서 멈추지 않고 Board API의 기본 CRUD 표면을 빠르게 완성하려는 흐름이다.
- 목록 조회에는 `title`, `user_id`, `tag`, `page`, `size` 기준을 먼저 잡았다.
- create/update 공통 검증을 `validate_board_request()`로 빼서 중복을 줄이려 했다.
- 삭제/수정 시 child row를 먼저 지워 FK 충돌을 피하려는 의도가 보인다.

고려하지 못한 것:

- repository가 조회, 검색, 수정, 삭제, DTO 변환까지 모두 맡아 책임이 많이 커졌다.
- `convert_to_board_response()`는 board마다 detail/user mapping을 별도 query로 조회하므로 목록 조회에서 N+1 query 위험이 있다.
- `UpdateBoard(CreateBoard)`는 수정도 모든 필드를 요구한다. `PUT` 전체 교체 정책인지 명시가 필요하다.
- update가 detail과 mapping을 삭제 후 재삽입하므로 단순하지만 비용이 크고 변경 단위가 거칠다.
- CRUD가 커졌지만 테스트가 없다.

개선 방향:

- create/list/detail/update/delete 최소 테스트를 먼저 추가한다.
- list query의 N+1 위험을 줄이기 위해 relationship, eager loading, bulk 조회 중 하나를 검토한다.
- `PUT` 전체 교체와 `PATCH` 부분 수정 정책을 분리한다.
- repository의 DTO 변환을 mapper 함수나 service로 분리할지 결정한다.

### 22. `8368026` - Schedule tasks only for schedule boards

구현한 것:

- `convert_to_board_response()`에서 schedule detail이 있을 때만 schedule task를 조회한다.
- `insert_board()`도 schedule detail 생성 블록 안에서만 task id를 응답 DTO로 변환한다.
- `BoardResponse.schedule_board_tasks` 타입을 `list[...] | None`으로 변경했다.

의도와 흐름:

- schedule task가 모든 board의 공통 응답 필드처럼 보이지 않도록, schedule board 전용 데이터로 제한하려는 의도다.
- 직전 CRUD 확장 후 응답 모양을 도메인 타입에 맞게 다시 조정한 흐름이다.

고려하지 못한 것:

- `None`과 빈 리스트 중 어떤 응답 정책을 쓸지 팀 기준이 필요하다.
- 클라이언트가 항상 list를 기대한다면 호환 문제가 생길 수 있다.
- update path의 schedule task 응답도 같은 정책으로 테스트해야 한다.

개선 방향:

- schedule board는 list, basic/proceedings board는 `None`으로 갈지 문서화한다.
- API 응답 테스트로 basic/proceedings/schedule 각각의 `schedule_board_tasks` 값을 고정한다.

### 23. `0d571f3` - RAG/GitHub domains scaffold

구현한 것:

- `backend/app/domains/rag/*`, `backend/app/domains/github/*` 기본 파일을 추가했다.
- GitHub 파일을 RAG 입력으로 바꾸기 위한 snapshot, chunk, pipeline 개념을 넣기 시작했다.

의도와 흐름:

- Board CRUD 이후 원래 README에 적어 둔 AI/RAG/GitHub 방향으로 넘어가려는 첫 전환점이다.

고려하지 못한 것:

- scaffold 범위가 넓고, 아직 API contract와 테스트가 부족하다.
- Board에서 RAG로 넘어가는 제품 흐름이 코드상 명확히 연결되지는 않았다.

개선 방향:

- RAG 입력, 출력, skip 조건을 DTO와 테스트로 먼저 고정한다.

### 24. `723927e` - GitHub RAG indexing pipeline

구현한 것:

- GitHub 파일을 snapshot으로 만들고 RAG evidence chunk로 변환하는 pipeline을 추가했다.
- `common/identity.py`, `common/validation.py`, `rag/pipeline.py`, RAG schema/service를 확장했다.

의도와 흐름:

- GitHub repository 파일을 검색 가능한 근거 단위로 만들려는 의도다.
- chunk identity와 citation을 두어 나중에 답변 출처를 추적하려 했다.

고려하지 못한 것:

- GitHub API 실패, rate limit, binary/large file 제외 정책이 아직 약하다.
- chunk 품질을 확인할 fixture test가 없다.

개선 방향:

- GitHub fixture 기반으로 text, markdown, python, binary, empty file 케이스를 나눈다.

### 25. `95cdb38` - RAG chunking modules split

구현한 것:

- RAG chunking을 `chunk_identity.py`, `chunking.py`, `python_classifier.py` 등으로 분리했다.

의도와 흐름:

- 커지는 RAG service를 작은 책임 단위로 쪼개려는 리팩터링이다.
- Python 코드는 class/function/import 같은 구조적 단위로 나누려는 방향이 보인다.

고려하지 못한 것:

- chunker별 입력/출력 규약이 테스트로 고정되지 않았다.

개선 방향:

- Python/Markdown chunker 각각에 snapshot fixture와 expected chunk snapshot test를 붙인다.

### 26. `696c85f` - RAG indexing services wiring

구현한 것:

- `container.py`를 추가해 dependency-injector 기반 service 조립을 시작했다.
- `ChunkFactory`, `ChunkCitationService`, `ChunkerRegistry`, `MarkdownChunker`,
  `PythonChunker`, `SnapshotValidator`, `ChunkingService`를 연결했다.
- `rag/router.py`와 `main.py`에 RAG route를 연결했다.

의도와 흐름:

- helper 묶음에서 실제 FastAPI route와 service 구조로 올리려는 단계다.

고려하지 못한 것:

- DI container가 생겼지만 test override와 env 설정 기준은 아직 없다.

개선 방향:

- container provider를 테스트에서 교체하는 패턴을 문서화한다.

### 27. `21b1961` - Source code comments

구현한 것:

- 주요 source file에 한국어 주석을 추가했다.

의도와 흐름:

- 혼자 AI 도움 없이 학습하면서 각 파일의 역할을 설명 가능하게 만들려는 흐름이다.

고려하지 못한 것:

- 주석은 이해에는 도움되지만, 테스트나 API contract를 대체하지 않는다.

개선 방향:

- 주석으로 설명한 책임을 테스트 이름과 문서 섹션으로도 고정한다.

### 28. `a5c4b66` - RAG indexes in SQL and vector DB

구현한 것:

- `RagIndexRun`, `RagFileSnapshot`, `RagChunk`, `RagSkippedFile` 모델을 추가했다.
- SQL repository와 Chroma vector repository를 추가했다.
- OpenAI embedding service와 Bruno API collection을 추가했다.

의도와 흐름:

- RAG를 단순 메모리 처리에서 재조회 가능한 저장 시스템으로 옮기는 핵심 커밋이다.
- SQL은 추적성과 원문 저장, vector DB는 검색성을 맡는 구조다.

고려하지 못한 것:

- SQL 저장과 vector 저장 사이의 부분 실패 보상 전략이 없다.
- embedding/vector DB/OpenAI 설정에 대한 `.env.example`이 필요하다.

개선 방향:

- SQL/vector 저장 통합 테스트와 실패 보상 정책을 먼저 잡는다.

### 29. `6b59517` - Layered pipeline and auth structure

구현한 것:

- GitHub OAuth, JWT, auth repository/service/router를 추가했다.
- 기능별 구조를 ports/service/external 중심으로 재정렬했다.

의도와 흐름:

- GitHub repository 접근을 사용자 OAuth token과 연결하려는 단계다.
- 외부 의존성을 ports로 감싸 테스트 가능한 구조를 만들려는 시도다.

고려하지 못한 것:

- auth, RAG, board 구조 재배치가 한 번에 들어와 회귀 위험이 크다.
- OAuth/JWT 설정 실패 시 사용자에게 보일 오류 기준이 약하다.

개선 방향:

- auth callback, token 발급, current-user 최소 테스트를 추가한다.
- `.env.example`에 GitHub OAuth/JWT 필수 값을 명시한다.

### 30. `53dfba1` - GitHub OAuth test console

구현한 것:

- frontend에 GitHub OAuth 테스트 화면을 추가했다.

의도와 흐름:

- backend auth 흐름을 브라우저에서 직접 확인하려는 실용적 장치다.

고려하지 못한 것:

- 테스트 console과 실제 제품 화면의 경계가 명확해야 한다.

개선 방향:

- dev/test 용도임을 UI 문구나 경로로 분리한다.

### 31. `ca6152c` - OAuth login screen localization

구현한 것:

- OAuth login 화면을 한국어 중심으로 정리했다.

의도와 흐름:

- 팀원이 직접 쓰는 화면으로 읽기 쉽게 바꾸려는 정리다.

고려하지 못한 것:

- auth 실패, callback 실패, token 만료 같은 상태별 메시지는 더 필요하다.

개선 방향:

- 성공/실패 상태 메시지를 API 오류 코드 기준과 맞춘다.

### 32. `0574d07` - Repository RAG answer workflow

구현한 것:

- repository RAG 답변 흐름, vector search, LLM answer generation, frontend repository workspace를 연결했다.

의도와 흐름:

- GitHub repository를 인덱싱하고 사용자가 질문하면 근거 기반 답변을 받는 제품 흐름을 만들려 했다.

고려하지 못한 것:

- RAG 답변이 어떤 run, branch, commit의 evidence를 쓰는지 처음에는 더 명확해야 했다.
- no evidence 상황에서 LLM이 추측하지 않도록 막는 분기가 필요했다.

개선 방향:

- `/rag/ask` 요청에 repository/branch/commit 기준을 명확히 하고, evidence 없는 케이스를 테스트한다.

### 33. `266b5c3` - Backend modules refactor and agent chat scaffold

구현한 것:

- `domains/*`를 `auth`, `board`, `github`, `rag`, `agent`, `shared` top-level module로 재배치했다.
- `api`, `service`, `domain`, `external`, `ports` 구조를 정리했다.
- `AgentChatService`, `InMemoryChatStore`, `EchoAgentResponder` 기반 agent chat scaffold를 추가했다.

의도와 흐름:

- 기능별 모듈 경계를 분명히 하고, agent 실험 입구를 마련하려는 커밋이다.

고려하지 못한 것:

- 파일 이동 폭이 커서 import 회귀 위험이 크다.
- echo responder는 실제 tool-using agent가 아니다.

개선 방향:

- module 이동 후 smoke test와 import test를 추가한다.
- agent scaffold와 RAG answer graph의 경계를 문서와 이름에서 분리한다.

### 34. `6b07845` - RAG study diagrams and notes

구현한 것:

- `docs/rag_study.md`, `docs/rag_ask_flow.md`, PlantUML diagram을 추가했다.

의도와 흐름:

- 구현한 RAG 흐름을 스스로 설명 가능한 문서로 만들려는 학습형 커밋이다.

고려하지 못한 것:

- 문서가 빠르게 바뀌는 코드와 동기화되지 않으면 stale해질 수 있다.

개선 방향:

- 주요 RAG route가 바뀔 때 문서의 요청/응답 예시도 같이 갱신한다.

### 35. `804d34f` - RAG answer flow through LangGraph

구현한 것:

- RAG answer flow를 `RagAnswerGraph`로 옮겼다.
- `retrieve_vector -> generate_answer -> build_response` 흐름을 graph로 표현했다.

의도와 흐름:

- RAG 답변 단계를 명시적인 graph node로 나누려는 시도다.

고려하지 못한 것:

- 이 시점의 graph는 아직 단순 직선 흐름이라 agent workflow라기보다 RAG workflow다.

개선 방향:

- evidence 없음, 재검색, query rewrite 같은 분기가 생길 때 LangGraph의 장점이 살아난다.

### 36. `7b51bd9` - RAG ask boundaries and run ids

구현한 것:

- `/rag/ask`의 경계와 `run_id`, repository/branch/commit 기준의 차이를 문서화했다.

의도와 흐름:

- 사용자가 직접 외워야 하는 값은 `run_id`가 아니라 repository/branch/commit이어야 한다는 판단이다.

고려하지 못한 것:

- 실제 코드도 commit 기준 evidence로 필터링되어야 문서와 일치한다.

개선 방향:

- 다음 커밋처럼 request DTO와 vector filter를 commit 기준으로 맞춘다.

### 37. `d0a73de` - Scope RAG ask by repository commit

구현한 것:

- `RagAskRequestDTO`에 repository/branch/commit 기준을 명확히 했다.
- vector search가 `repository_full_name`, `branch`, `commit_sha` metadata filter를 사용하게 했다.
- Bruno, frontend, 문서도 commit 기준 질문 흐름으로 맞췄다.

의도와 흐름:

- RAG 답변을 사용자가 보고 있는 코드 버전과 같은 commit evidence로 제한하려는 핵심 보강이다.

고려하지 못한 것:

- commit 없이 branch만 들어왔을 때 latest run 선택 기준은 사용자 기대와 다를 수 있다.

개선 방향:

- exact commit, branch latest, missing run 케이스를 테스트로 고정한다.

### 38. `1865d09` - Branch answer graph on evidence

구현한 것:

- `RagAnswerGraph`가 vector 검색 후 evidence 존재 여부로 분기한다.
- evidence가 있으면 LLM 답변을 생성하고, 없으면 no-evidence 응답을 만든다.

의도와 흐름:

- 근거 없는 질문에 LLM이 추측 답변을 하지 않도록 막으려는 안전 장치다.

고려하지 못한 것:

- no-evidence 상황에서 query rewrite나 SQL keyword fallback은 아직 없다.

개선 방향:

- no-evidence branch를 테스트하고, 이후 재검색 전략을 붙일지 결정한다.

### 39. `842d495` - Duplicate RAG index storage skip

구현한 것:

- `RagIndexService.find_existing_run()`으로 같은 repository/branch/commit 기존 run을 찾는다.
- 기존 run이 있으면 GitHub 수집, chunk 생성, SQL/vector 저장을 다시 하지 않고 `reused=True`로 응답한다.
- SQL/vector repository의 count/exact-run 조회와 frontend/Bruno 응답 확인 흐름을 보강했다.

의도와 흐름:

- 같은 commit을 반복 인덱싱해 저장소와 비용을 늘리는 문제를 줄이려는 보강이다.

고려하지 못한 것:

- application-level check만으로는 동시 요청 race condition을 막기 어렵다.
- DB unique constraint 또는 idempotency lock이 필요하다.

개선 방향:

- `repository_full_name + branch + commit_sha` unique constraint를 추가한다.
- duplicate request 동시성 테스트를 추가한다.
- SQL/vector 저장 중 하나만 성공하는 실패 케이스를 정한다.

## 현재까지 보이는 강점

- 큰 제품 방향을 먼저 잡고 작은 구현 단위로 내려오고 있다.
- 일반 협업 보드의 기본 모델을 만든 뒤 RAG/GitHub/Auth/Agent로 확장했다.
- 기능별 module과 `api`, `service`, `domain`, `external`, `ports` 계층을 나누는 감각이 있다.
- DB constraint와 Pydantic validation을 함께 생각하기 시작했다.
- 잘못된 구현을 조금씩 고치는 흐름이 있다.
  - 예: task FK를 `schedule_board_detail.board_id`로 수정
  - 예: `return {"msg": ...}`에서 `BoardResponse`로 이동
  - 예: `board_type`/detail 조합 검증 추가
  - 예: 함수명과 겹치던 router 지역 변수를 `created_board`로 수정
  - 예: 실제 DB 저장으로 가기 위한 session factory 추가
  - 예: create 이후 CRUD/search/pagination으로 API 표면 확장
  - 예: schedule task 응답을 schedule board 전용으로 보정
- RAG chunk identity, citation, SQL/vector 저장, commit scope를 고려했다.
- `/rag/ask`가 특정 repository/branch/commit evidence 안에서만 답하도록 범위를 좁힌 점이 좋다.
- evidence 없음 분기를 LangGraph에 명시해 근거 없는 답변을 줄이려 했다.
- 중복 RAG index 재사용으로 비용과 저장소 팽창을 줄이려 했다.

## 현재까지 보이는 약점

- CRUD 흐름이 생겼지만, 아직 학습용 초기화와 테스트 공백이 크다.
- 모델, DTO, service, repository를 끝까지 잇는 실행 경로는 생겼지만 repository 책임 경계가 더 두꺼워졌다.
- 목록 조회의 `convert_to_board_response()`는 N+1 query 위험이 있다.
- update가 전체 교체인지 부분 수정인지 정책이 명확하지 않다.
- `User`, 인증, DB session처럼 다른 도메인과 만나는 지점에서 막힐 가능성이 크다.
- HTTP status 기준, 예외 책임, DTO 검증 위치 같은 팀 규칙이 아직 코드에 반영되지 않았다.
- `board_type` 값 기준이 여러 파일에 흩어져 있어 값 변경 시 불일치가 생길 수 있다.
- 테스트가 없어 지금 넣은 검증이 다음 수정에서 깨져도 잡기 어렵다.
- RAG/Auth/Agent/refactor가 짧은 시간에 동시에 들어와 import 회귀와 API 회귀 위험이 크다.
- OAuth/JWT/OpenAI/Chroma/GitHub API 설정에 필요한 `.env.example`과 실패 메시지 기준이 부족하다.
- SQL 저장과 vector 저장 사이의 부분 실패 보상 전략이 없다.
- duplicate index reuse는 DB unique constraint 없이 동시 요청 race condition에 취약하다.
- agent chat scaffold는 아직 echo/memory 수준이라 실제 RAG agent나 MCP tool executor로 보기 어렵다.

## 지금 고치는 순서

1. RAG indexing과 `/rag/ask` 흐름을 테스트로 고정한다.
   - repository index store 성공
   - duplicate index reused
   - exact commit evidence found
   - no evidence
   - branch latest run
   - invalid repository/auth 실패
2. `repository_full_name + branch + commit_sha` unique constraint 또는 idempotency lock을 둔다.
3. SQL/vector 저장 부분 실패 보상 기준을 정한다.
4. `.env.example`에 GitHub OAuth, JWT, OpenAI, Chroma, PostgreSQL 설정을 명시한다.
5. Agent scaffold와 RAG answer graph의 경계를 문서와 route 이름에서 분리한다.
6. Board CRUD 흐름을 테스트로 고정한다.
   - basic board create
   - schedule board create
   - proceedings board create
   - list pagination
   - detail 404
   - update detail/mapping 교체
   - delete 후 재조회 404
   - schedule task 없는 요청
   - 잘못된 detail 조합
7. `schedule_board_tasks` 응답 정책을 정한다.
   - schedule board는 list
   - basic/proceedings board는 `None` 또는 빈 list 중 하나로 고정
8. `User` 기준을 정한다.
   - JWT 전 임시 user table을 둘지
   - auth 구현 전까지 `user_id`를 mock으로 둘지
9. body validation을 `schema.py`로 옮긴다.
   - `board_type` invalid
   - basic board detail/task 포함
   - detail 누락
   - detail 혼합
   - `start_at >= end_at`
   - 실패 status는 `422`
10. service/repository 책임을 줄인다.
   - request body 모양 검증은 schema
   - DB 조회/저장 규칙은 service
   - HTTP status 변환은 router
   - ORM -> DTO 변환은 mapper 함수로 분리 검토
11. list query의 N+1 위험을 줄인다.
   - relationship/eager loading
   - bulk 조회
   - response mapper 최적화
12. MCP와 실제 agent 실행 기록은 현재 RAG 저장 모델과 별도 테이블로 붙인다.
   - `AgentRun`
   - `ToolCall`
   - `McpServer`
   - `McpTool`

## 민정에게 줄 수 있는 피드백

> 지금 흐름은 Board CRUD에서 RAG/GitHub/Auth까지 확장된 게 보인다.
> 특히 `/rag/ask`를 repository/branch/commit evidence로 제한한 건 맞는 방향이야.
> 이제 범위를 더 넓히기보다 테스트와 운영 기준을 고정해야 해.
> duplicate index reuse는 unique constraint나 idempotency lock으로 막고,
> SQL/vector 저장 중 하나만 성공하는 실패 케이스를 정하자.
> LangGraph를 쓴다고 바로 agent가 되는 건 아니니까, 지금은 RAG answer graph와
> agent scaffold를 분리해서 설명하는 게 맞아.
