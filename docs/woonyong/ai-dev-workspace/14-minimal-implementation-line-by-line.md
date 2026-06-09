# 최소 구현 라인별 해설

기준: 2026-06-10 현재 최소 파이프라인 구현.

이 문서는 자동 생성 파일, lock 파일, 빈 `__init__.py`를 제외하고 사람이 읽어야 하는 최소 구현 파일을 라인별로 설명한다.

## 먼저 이해할 구조

현재 구현은 실제 GitHub, DB, Redis queue, pgvector, LLM을 완성한 상태가 아니다.

지금은 아래 흐름이 코드로 끝까지 연결되는지 확인하는 골격이다.

```text
FastAPI route
  -> PipelineService
  -> RepoSyncService
  -> CodeIndexService
  -> RagIndexService
  -> AgentProposalService
  -> ApprovalService
  -> PublishService
  -> PipelineResponse
```

객체지향 관점에서는 다음처럼 보면 된다.

- `schemas/pipeline.py`: DTO, 즉 요청/응답 데이터 모양.
- `modules/*/service.py`: 실제 일을 하는 객체.
- `modules/pipeline/ports.py`: 각 service가 지켜야 하는 인터페이스 역할.
- `modules/pipeline/service.py`: 여러 service 객체를 조합하는 application service.
- `main.py`: FastAPI route, Java식 Controller에 가장 가깝다.

## `.mise.toml`

- 1: mise의 tool 버전 섹션을 시작한다.
- 2: Node.js 버전을 24.16.0으로 고정한다.
- 3: pnpm 버전을 10.17.0으로 고정한다.
- 4: Python 버전을 3.12로 고정한다.
- 5: uv 버전을 0.9.17로 고정한다.
- 7: `mise run setup` task를 정의한다.
- 8: setup task 설명이다.
- 9: setup에서 실행할 명령 배열을 시작한다.
- 10: corepack을 켜서 pnpm 실행을 안정화한다.
- 11: frontend/workspace 의존성을 설치한다.
- 12: backend Python 의존성을 uv로 설치한다.
- 13: setup 명령 배열을 닫는다.
- 15: `mise run compose:config` task를 정의한다.
- 16: Docker Compose 설정 검증 task 설명이다.
- 17: compose 설정을 조용히 검증한다.
- 19: `mise run compose:up` task를 정의한다.
- 20: 로컬 RepoPilot 파이프라인 시작 task 설명이다.
- 21: 이미지를 build하고 compose 서비스를 띄운다.
- 23: `mise run compose:down` task를 정의한다.
- 24: compose 서비스 종료 task 설명이다.
- 25: compose 서비스를 내린다.
- 27: `mise run compose:logs` task를 정의한다.
- 28: 로그 follow task 설명이다.
- 29: compose 로그를 계속 따라본다.
- 31: `mise run api:test` task를 정의한다.
- 32: backend test task 설명이다.
- 33: 명령 실행 위치를 `backend`로 바꾼다.
- 34: pytest를 실행한다.
- 36: `mise run web:typecheck` task를 정의한다.
- 37: web typecheck task 설명이다.
- 38: web package만 TypeScript typecheck한다.
- 40: `mise run check` task를 정의한다.
- 41: 가벼운 전체 확인 task 설명이다.
- 42: compose config, backend test, web typecheck를 순서대로 실행한다.

## `compose.yaml`

- 1: Docker Compose 프로젝트 이름을 `repopilot`으로 둔다.
- 3: backend 계열 서비스가 공유할 환경변수 anchor를 시작한다.
- 4: 실행 환경 기본값을 local로 둔다.
- 5: backend에서 쓸 Postgres 연결 문자열이다.
- 6: backend에서 쓸 Redis 연결 문자열이다.
- 7: OpenAI API key 자리다. 실제 값은 `.env`에 둔다.
- 8-10: GitHub App 연동을 위한 값 자리다.
- 12: backend 계열 서비스 공통 설정 anchor를 시작한다.
- 13: backend image 이름이다.
- 14-15: backend Dockerfile build context를 지정한다.
- 16-17: 위에서 정의한 backend 환경변수를 주입한다.
- 18-22: postgres와 redis가 healthy가 된 뒤 backend 서비스가 시작되게 한다.
- 24: 실제 services 섹션을 시작한다.
- 25-40: web 서비스다. Next.js 앱을 3000번 포트로 띄우고 api health 이후 시작한다.
- 42-55: api 서비스다. FastAPI를 uvicorn reload 모드로 8000번 포트에 띄우고 healthcheck를 건다.
- 57-61: repo sync worker다. 현재는 heartbeat runner를 실행한다.
- 63-67: code index worker다.
- 69-73: RAG index worker다.
- 75-79: agent proposal worker다.
- 81-85: static publish worker다.
- 87-103: PostgreSQL + pgvector 서비스다.
- 88: pgvector가 포함된 PostgreSQL 16 이미지를 쓴다.
- 89-92: DB 사용자, 비밀번호, DB 이름 기본값이다.
- 93-94: 로컬 호스트에서만 5432를 연다.
- 95-97: DB data volume과 init SQL 폴더를 연결한다.
- 98-103: Postgres healthcheck다.
- 104-115: Redis 서비스다.
- 105: Redis 7 alpine 이미지를 쓴다.
- 106: appendonly 모드로 실행한다.
- 107-108: 로컬 호스트에서만 6379를 연다.
- 109-110: Redis data volume이다.
- 111-115: Redis healthcheck다.
- 117-122: compose가 관리할 named volume 목록이다.

## `backend/pyproject.toml`

- 1: Python project metadata 섹션을 시작한다.
- 2: backend package 이름이다.
- 3: backend version이다.
- 4: 설명이다.
- 5: Python 3.12 이상, 3.13 미만만 허용한다.
- 6: runtime dependency 목록을 시작한다.
- 7: async PostgreSQL driver다.
- 8: FastAPI framework다.
- 9: HTTP client/test 관련 dependency다.
- 10: pgvector Python package다.
- 11: settings 관리용 Pydantic package다.
- 12: Redis client다.
- 13: async SQLAlchemy다.
- 14: structured logging package다.
- 15: CLI helper package다.
- 16: ASGI server인 uvicorn이다.
- 17: runtime dependency 목록을 닫는다.
- 19: dependency group 섹션을 시작한다.
- 20-24: dev dependency로 pytest, pytest-asyncio, ruff를 둔다.
- 26: pytest 설정 섹션이다.
- 27: 테스트 폴더를 `tests`로 지정한다.
- 28: import 기준 경로를 backend root로 둔다.
- 30: ruff 설정 섹션이다.
- 31: line length를 100으로 둔다.
- 32: Python 3.12 기준으로 lint rule을 적용한다.

## `backend/Dockerfile`

- 1: Python 3.12 slim 이미지를 base stage로 쓴다.
- 3: `.pyc` 파일 생성을 막는다.
- 4: stdout/stderr buffering을 줄여 로그가 바로 보이게 한다.
- 5: uv가 dependency를 copy 방식으로 연결하게 한다.
- 6: container PATH에 `/app/.venv/bin`을 앞에 둔다.
- 8: 작업 디렉터리를 `/app`으로 둔다.
- 10: uv를 설치한다.
- 12: dependency lock 관련 파일만 먼저 복사한다.
- 13: lockfile 기준으로 runtime dependency만 설치한다.
- 15: backend app 코드를 복사한다.
- 17: container가 8000번 포트를 쓴다고 문서화한다.
- 19: 기본 실행 명령은 uvicorn으로 FastAPI app을 띄우는 것이다.

## `backend/app/main.py`

- 1: FastAPI 앱 클래스를 가져온다.
- 3: 파이프라인 전체를 실행하는 application service를 가져온다.
- 4: stage 목록을 API 응답용 dict로 바꿔주는 helper를 가져온다.
- 5: 요청/응답 DTO인 `PipelineRequest`, `PipelineResponse`를 가져온다.
- 7: FastAPI 앱 객체를 만든다. 이 객체가 ASGI 서버에서 실행된다.
- 8: OpenAPI 문서에 표시될 API 이름이다.
- 9: API 버전이다.
- 10: API 요약 설명이다.
- 11: FastAPI 생성자 호출을 끝낸다.
- 13: `PipelineService` 객체를 한 번 만든다. route는 이 객체에게 일을 맡긴다.
- 16: `GET /health` route를 등록한다.
- 17: health handler 함수다. 반환 타입은 문자열 dict다.
- 18: 서버가 살아 있으면 `{status: ok}`를 반환한다.
- 21: `GET /pipeline` route를 등록한다.
- 22: stage 목록을 반환하는 handler다.
- 23: 공통 stage 정의를 API 응답 형태로 변환해 반환한다.
- 26: `POST /pipeline/run` route를 등록한다.
- 27: 요청 body를 `PipelineRequest`로 검증하고 받는다.
- 28: 실제 파이프라인 실행은 `PipelineService.run()`에 위임한다.

## `backend/app/schemas/pipeline.py`

- 1: Pydantic의 `BaseModel`과 `Field`를 가져온다.
- 4: repo 안의 파일 하나를 표현하는 DTO다.
- 5: 파일 경로다.
- 6: 파일 내용이다.
- 9: 기본 요청에 넣을 sample 파일 목록을 만드는 함수다.
- 10: 기본 파일 리스트를 반환하기 시작한다.
- 11-14: Python 코드 예시 파일을 만든다.
- 15-18: Markdown 문서 예시 파일을 만든다.
- 19: 기본 파일 리스트를 끝낸다.
- 22: `/pipeline/run` 요청 DTO다.
- 23: repository 기본값은 `sample-repo`다.
- 24: branch 기본값은 `main`이다.
- 25: files 기본값은 `default_files()`로 만든다. list를 직접 기본값으로 두지 않기 위해 `default_factory`를 쓴다.
- 28: repo sync 결과 DTO다.
- 29: repository 이름이다.
- 30: branch 이름이다.
- 31: 현재 최소 구현에서 만든 가짜 commit sha다.
- 32: snapshot에 포함된 파일 목록이다.
- 35: 코드 참조 DTO다.
- 36: 참조 id다. 현재는 `path:symbol` 형태다.
- 37: 참조가 있는 파일 경로다.
- 38: 함수명 또는 `file` 같은 symbol 이름이다.
- 39: symbol이 발견된 줄 번호다.
- 40: 어떤 commit 기준인지 나타낸다.
- 41: 참조 상태다. 현재는 `verified`만 쓴다.
- 44: RAG 검색에 들어갈 chunk DTO다.
- 45: chunk id다.
- 46: chunk 원본 파일 경로다.
- 47: 검색 컨텍스트로 쓸 텍스트다.
- 48: 답변 근거로 표시할 citation이다.
- 51: AI가 만든 제안 DTO다.
- 52: proposal id다.
- 53: proposal 종류다.
- 54: 승인 상태다. 현재는 `pending`에서 `approved`로 바뀐다.
- 55: 제안 대상 파일 경로다.
- 56: 제안의 근거 citation 목록이다.
- 57: 신뢰도 점수다.
- 58: 제안 문장이다.
- 61: publish 결과 DTO다.
- 62: publish snapshot id다.
- 63: publish 상태다.
- 64: publish 결과 경로다.
- 65: publish에 포함된 item 수다.
- 66: publish에 포함된 proposal 수다.
- 69: stage 실행 결과 DTO다.
- 70: stage id다.
- 71: stage 상태다.
- 72: stage별 상세값이다.
- 75: `/pipeline/run` 최종 응답 DTO다.
- 76-81: repo snapshot, code references, retrieval chunks, proposals, publish snapshot, stages를 하나의 응답으로 묶는다.

## `backend/app/pipeline.py`

- 1: dataclass를 dict로 바꾸는 `asdict`와 dataclass decorator를 가져온다.
- 2: stage detail 입력 타입으로 `Mapping`을 가져온다.
- 4: stage 결과 DTO를 가져온다.
- 7: `PipelineStage`를 dataclass로 선언한다.
- 8: stage 하나를 표현하는 값 객체다.
- 9: stage id다.
- 10: 화면에 보일 stage 이름이다.
- 11: stage 목적 설명이다.
- 14: 전체 pipeline stage 목록이다. stage 순서의 원본이다.
- 15-19: repo sync stage다.
- 20-24: code index stage다.
- 25-29: RAG index stage다.
- 30-34: agent proposal stage다.
- 35-39: approval stage다.
- 40-44: static publish stage다.
- 47: stage id만 tuple로 뽑는다. 테스트와 응답 순서 검증에 쓴다.
- 48-50: worker가 있는 stage만 뽑는다. `approval`은 worker가 아니라 승인 단계라 제외한다.
- 53: stage 목록을 API 응답 dict list로 바꾸는 함수다.
- 54: dataclass 객체들을 dict로 변환한다.
- 57: 모든 stage를 `done` 상태로 만드는 helper다.
- 58-61: `PIPELINE_STAGE_IDS` 순서대로 `StageResult`를 만든다.

## `backend/app/modules/pipeline/ports.py`

- 1: Python의 구조적 인터페이스인 `Protocol`을 가져온다.
- 3-10: 각 port 메서드에서 쓰는 DTO 타입을 가져온다.
- 13: repo sync service가 지켜야 할 인터페이스다.
- 14: `sync(request) -> RepoSnapshot` 메서드가 있어야 함을 선언한다.
- 17: code index service 인터페이스다.
- 18: `index(snapshot) -> list[CodeReference]` 메서드가 있어야 한다.
- 21: RAG index service 인터페이스다.
- 22-26: repo snapshot과 code references를 받아 retrieval chunks를 반환해야 한다.
- 29: agent proposal service 인터페이스다.
- 30-34: code references와 chunks를 받아 proposals를 반환해야 한다.
- 37: approval service 인터페이스다.
- 38: proposals를 받아 승인 처리된 proposals를 반환해야 한다.
- 41: publish service 인터페이스다.
- 42-47: snapshot, chunks, proposals를 받아 publish snapshot을 반환해야 한다.

## `backend/app/modules/pipeline/service.py`

- 1: `dataclass`, `field`를 가져온다. 생성자 주입과 값 객체에 쓴다.
- 3-5: 실제 구현 service 클래스들을 가져온다.
- 6-13: service가 따라야 할 port 타입들을 가져온다.
- 14-16: publish, RAG, repo sync 실제 구현 service를 가져온다.
- 17: stage 결과 helper를 가져온다.
- 18-26: 파이프라인에서 오가는 DTO 타입을 가져온다.
- 29: `PipelineArtifacts`를 불변 dataclass로 만든다.
- 30: 파이프라인 중간 산출물을 담는 값 객체다.
- 31-36: 각 단계 산출물을 필드로 가진다.
- 39: `PipelineService`를 dataclass로 만든다. `slots=True`는 불필요한 동적 속성 생성을 막는다.
- 40: 전체 파이프라인 application service다.
- 41-46: 각 dependency를 port 타입으로 선언하고 기본 구현은 `default_factory`로 만든다.
- 48: route에서 호출하는 공개 메서드다.
- 49: 내부 stage들을 실행해 산출물을 모은다.
- 51-58: 산출물을 `PipelineResponse` DTO로 변환해 반환한다.
- 60: 실제 stage 실행 순서를 담은 private 메서드다.
- 61: repo sync를 실행한다.
- 62: code index를 실행한다.
- 63: RAG index를 실행한다.
- 64: agent proposal을 만든다.
- 65: proposal 승인 처리를 한다.
- 66: publish snapshot을 만든다.
- 68-75: 중간 산출물을 `PipelineArtifacts`로 묶어 반환한다.
- 77: stage 결과 detail을 만드는 private 메서드다.
- 78-85: 각 stage id별 상세값을 dict로 만든다.

## `backend/app/modules/repo_sync/service.py`

- 1: sha1 해시 함수를 가져온다.
- 3: 요청 DTO와 repo snapshot DTO를 가져온다.
- 6: repo sync 역할을 맡는 service 객체다.
- 7: 요청을 받아 repo snapshot을 반환하는 메서드다.
- 8: sha1 digest 객체를 만든다.
- 9: repository 이름을 digest에 넣는다.
- 10: branch 이름을 digest에 넣는다.
- 12: 요청에 들어온 파일을 하나씩 돈다.
- 13: 파일 경로를 digest에 넣는다.
- 14: 파일 내용을 digest에 넣는다.
- 16-21: repository, branch, 짧은 commit sha, files를 가진 `RepoSnapshot`을 반환한다.

## `backend/app/modules/code_index/service.py`

- 1: code reference와 repo snapshot DTO를 가져온다.
- 4: 코드 색인 service 객체다.
- 5: repo snapshot을 받아 code references를 반환한다.
- 6: 결과를 담을 리스트다.
- 8: snapshot 안의 파일을 하나씩 본다.
- 9: 파일 내용에서 symbol을 추출한다.
- 11: symbol이 없는 파일인지 확인한다.
- 12-21: symbol이 없으면 파일 자체를 `file` symbol로 등록한다.
- 22: 이미 파일 참조를 추가했으니 다음 파일로 넘어간다.
- 24: symbol이 있으면 symbol별로 반복한다.
- 25-34: path, symbol, line, commit sha, verified 상태를 가진 `CodeReference`를 추가한다.
- 36: code references 전체를 반환한다.
- 38: 파일 내용에서 symbol 이름과 line을 추출하는 private 메서드다.
- 39: 추출 결과 리스트다.
- 41: 파일 내용을 줄 단위로 돌면서 1부터 line number를 붙인다.
- 42: 앞뒤 공백을 제거한다.
- 43-44: `async def` 함수명을 추출한다.
- 45-46: `def` 함수명을 추출한다.
- 47-48: JavaScript `function` 함수명을 추출한다.
- 49-50: `export function` 함수명을 추출한다.
- 52: symbol 목록을 반환한다.

## `backend/app/modules/rag_index/service.py`

- 1: RAG chunk 생성에 필요한 DTO 타입을 가져온다.
- 4: RAG index 역할의 service 객체다.
- 5-9: repo snapshot과 code references를 받아 retrieval chunks를 반환한다.
- 10: 참조된 파일 path만 set으로 만든다.
- 11: 결과 chunk 리스트다.
- 13: snapshot 파일을 하나씩 본다.
- 14-15: code reference에 없는 파일은 검색 chunk에서 제외한다.
- 17: 파일 내용의 앞뒤 공백을 제거한다.
- 18-19: 빈 파일이면 제외한다.
- 21-28: chunk id, source path, 최대 800자 text, citation을 가진 `RetrievalChunk`를 추가한다.
- 30: chunk 목록을 반환한다.

## `backend/app/modules/agent/service.py`

- 1: proposal, code reference, retrieval chunk DTO를 가져온다.
- 4: AI proposal 생성 역할의 service 객체다.
- 5-9: references와 chunks를 받아 proposals를 반환한다.
- 10-11: 참조가 없으면 제안도 없으므로 빈 리스트를 반환한다.
- 13: 현재 최소 구현에서는 첫 번째 reference만 대상으로 삼는다.
- 14: 해당 파일 path와 같은 chunk citation을 evidence로 모은다.
- 16-26: 관련 코드 제안 proposal 하나를 만든다.
- 18: proposal id는 reference id를 기반으로 만든다.
- 19: proposal 종류를 지정한다.
- 20: 처음 상태는 `pending`이다.
- 21: 제안 대상 파일 경로다.
- 22: 근거 citation 목록이다.
- 23: evidence가 있으면 0.7, 없으면 0.4로 confidence를 둔다.
- 24: 사용자에게 보여줄 제안 문장이다.

## `backend/app/modules/approval/service.py`

- 1: proposal DTO를 가져온다.
- 4: 승인 처리 service 객체다.
- 5: proposal 목록을 받아 proposal 목록을 반환한다.
- 6: Pydantic `model_copy`로 원본을 직접 바꾸지 않고 status만 `approved`인 새 객체를 만든다.

## `backend/app/modules/publish/service.py`

- 1: publish에 필요한 DTO 타입들을 가져온다.
- 4: publish 역할의 service 객체다.
- 5-10: snapshot, chunks, proposals를 받아 publish snapshot을 반환한다.
- 11: repository 이름에 `/`가 있으면 publish path에 안전하도록 `-`로 바꾼다.
- 13-19: publish id, 상태, path, item count, proposal count를 가진 `PublishSnapshot`을 반환한다.

## `backend/app/workers/runner.py`

- 1: CLI argument parser를 가져온다.
- 2: 비동기 이벤트 루프를 쓰기 위해 `asyncio`를 가져온다.
- 3: 종료 signal 처리를 위해 `signal`을 가져온다.
- 5: stage 목록과 worker 가능한 stage id 목록을 가져온다.
- 8: CLI 인자를 파싱하는 함수다.
- 9: parser 설명을 만든다.
- 10-14: 첫 번째 위치 인자 `kind`를 받되 `WORKER_STAGE_IDS` 안의 값만 허용한다.
- 15: 파싱 결과를 반환한다.
- 18: worker 실행 coroutine이다.
- 19: 종료를 기다릴 event를 만든다.
- 20: 현재 실행 중인 event loop를 가져온다.
- 22-23: SIGINT, SIGTERM이 들어오면 stop event를 켜도록 등록한다.
- 25: kind와 일치하는 stage 객체를 찾는다.
- 26: worker 시작 로그를 출력한다.
- 28: stop event가 켜질 때까지 반복한다.
- 29-30: 최대 60초 동안 stop event를 기다린다.
- 31-32: 60초 동안 종료 신호가 없으면 heartbeat를 출력한다.
- 34: 종료 로그를 출력한다.
- 37: 동기 entry point다.
- 38: CLI 인자를 읽는다.
- 39: async worker를 실행한다.
- 42-43: 파일이 직접 실행될 때만 `main()`을 호출한다.

## `backend/tests/test_pipeline.py`

- 1: FastAPI 테스트 클라이언트를 가져온다.
- 3: 실제 FastAPI app 객체를 가져온다.
- 4: stage id 원본을 가져온다.
- 7: 테스트 클라이언트를 만든다.
- 10: health check 테스트다.
- 11: `/health`를 호출한다.
- 13: HTTP 200인지 확인한다.
- 14: 응답 body가 정확한지 확인한다.
- 17: `/pipeline` stage 목록 테스트다.
- 18: `/pipeline`을 호출한다.
- 20: HTTP 200인지 확인한다.
- 21: 응답에서 stage id만 뽑는다.
- 22: stage 순서가 원본과 같은지 확인한다.
- 23: stage id 중복이 없는지 확인한다.
- 26: `/pipeline/run` 전체 흐름 테스트다.
- 27: 빈 JSON으로 실행한다. 기본값 때문에 sample repo가 사용된다.
- 29: HTTP 200인지 확인한다.
- 30: JSON body를 변수로 둔다.
- 31: 기본 repository 이름을 확인한다.
- 32: code references가 비어 있지 않은지 확인한다.
- 33: retrieval chunks가 비어 있지 않은지 확인한다.
- 34: 첫 proposal이 approved인지 확인한다.
- 35: publish snapshot이 published인지 확인한다.
- 36: 실행 결과 stage 순서가 원본과 같은지 확인한다.

## `apps/web/src/app/page.tsx`

- 1: 화면에 표시할 stage 배열을 선언한다.
- 2-6: repo sync stage 표시 데이터다.
- 7-11: code index stage 표시 데이터다.
- 12-16: RAG index stage 표시 데이터다.
- 17-21: agent proposal stage 표시 데이터다.
- 22-26: approval stage 표시 데이터다.
- 27-31: static publish stage 표시 데이터다.
- 32: `as const`로 stage 배열을 readonly literal 타입처럼 고정한다.
- 34: Next.js app route의 Home 컴포넌트다.
- 35: JSX 반환을 시작한다.
- 36: main 영역이다.
- 37: 본문 폭을 잡는 shell section이다.
- 38: 작은 상단 라벨이다.
- 39: 페이지 제목이다.
- 40-44: 현재 화면이 제품 UI가 아니라 파이프라인 확인용임을 설명한다.
- 45: stage 목록을 담는 ul이다.
- 46: stage 배열을 반복한다.
- 47: 각 stage를 li로 그린다. key는 중복 방지를 위해 `stage.id`를 쓴다.
- 48: stage 이름을 굵게 표시한다.
- 49: stage 설명을 표시한다.
- 50-52: li, map, ul을 닫는다.
- 53-55: section, main, return을 닫는다.
- 56: Home 컴포넌트를 끝낸다.

## `apps/web/src/app/layout.tsx`

- 1: Next.js metadata 타입을 가져온다.
- 2: 전역 CSS를 불러온다.
- 4: 페이지 metadata를 선언한다.
- 5: 브라우저 title이다.
- 6: description metadata다.
- 7: metadata 객체를 닫는다.
- 9: 전체 HTML layout 컴포넌트다.
- 10: 하위 page/component가 들어올 `children`이다.
- 11-13: children prop 타입을 readonly로 둔다.
- 14: JSX 반환을 시작한다.
- 15: HTML 언어를 한국어로 지정한다.
- 16: body 안에 children을 넣는다.
- 17-19: html, return, component를 닫는다.

## `apps/web/src/app/globals.css`

- 1: 전역 CSS 변수 scope를 시작한다.
- 2: 브라우저 color scheme을 light로 둔다.
- 3-7: 배경, 글자, 보조 글자, 선, 강조색 변수를 정의한다.
- 8: `:root`를 닫는다.
- 10-12: 모든 요소에 `box-sizing: border-box`를 적용한다.
- 14-19: body 기본 margin, 배경, 글자색, font를 지정한다.
- 21-24: main이 화면 높이를 채우고 padding을 갖게 한다.
- 26-29: `.shell`은 본문 최대 폭과 가운데 정렬을 담당한다.
- 31-36: `.eyebrow` 작은 라벨 스타일이다.
- 38-44: h1 크기, 폭, line-height를 잡는다.
- 46-52: summary 문단의 폭, 여백, 색, 글자 크기, line-height를 잡는다.
- 54-61: pipeline 목록을 responsive grid로 만든다.
- 63-68: 각 stage card의 높이, padding, border, background를 지정한다.
- 70-73: stage 이름을 block으로 두고 아래 여백을 준다.
- 75-79: stage 설명 글자색, 크기, line-height를 지정한다.
- 81-89: 모바일에서 main padding과 h1 font-size를 줄인다.

## `apps/web/package.json`

- 1: JSON 객체를 시작한다.
- 2: web package 이름이다.
- 3: web package version이다.
- 4: private package라 publish하지 않는다.
- 5: ESM module 기준이다.
- 6-11: dev, build, start, typecheck script를 정의한다.
- 12-16: Next.js, React, React DOM runtime dependency다.
- 17-22: TypeScript와 타입 패키지 dev dependency다.
- 23: JSON 객체를 닫는다.

## `apps/web/Dockerfile`

- 1: Node 24 alpine 이미지를 base로 쓴다.
- 2: 작업 디렉터리를 `/repo`로 둔다.
- 3: corepack을 켜서 pnpm을 쓸 수 있게 한다.
- 5: workspace dependency 파일을 복사한다.
- 6: web package manifest를 복사한다.
- 7: web package에 필요한 dependency를 lockfile 기준으로 설치한다.
- 9: web app source를 복사한다.
- 11: 3000번 포트를 쓴다고 문서화한다.
- 12: pnpm filter로 web dev server를 0.0.0.0:3000에 띄운다.

## 객체지향적으로 더 발전시키는 방향

현재 반영된 OOP 구조는 최소 단계다.

다음 단계에서 실제 구현을 붙일 때는 이렇게 확장한다.

- `RepoSyncPort` 구현체를 `GitHubRepoSyncService`로 교체한다.
- `CodeIndexPort` 구현체를 tree-sitter 기반 indexer로 교체한다.
- `RagIndexPort` 구현체를 pgvector 저장/검색 use case로 교체한다.
- `AgentProposalPort` 구현체를 LLM client와 retrieval client를 조합하는 service로 교체한다.
- `ApprovalPort`는 user permission과 audit log를 확인하는 service로 바꾼다.
- `PublishPort`는 실제 static archive 파일을 만드는 service로 바꾼다.

핵심은 `PipelineService`가 구체 구현을 직접 알지 않고 port만 알게 하는 것이다.
이렇게 하면 테스트에서는 fake service를 넣고, 운영에서는 실제 GitHub/DB/AI service를 넣을 수 있다.
