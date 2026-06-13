# RepoPilot Repo RAG 구축 통합 계획서

## Summary

목표는 GitHub OAuth로 선택한 repo를 기준으로 branch, 문서, 코드, 이슈, PR, 커밋을 자동 분석하는 **repo-first RAG 기반 프로젝트 지식 서비스**로 RepoPilot을 발전시키는 것이다.

RepoPilot은 Notion 복제가 아니라, 사용자가 선택한 GitHub repo의 구현 문서, 작업 기록, 코드 참조, 이슈/PR/커밋을 연결해 **"현재 repo 상태에서 무엇이 구현됐고, 어떤 문서가 낡았고, 다음 action은 무엇인지"** 보여주는 도구다. 현재 구현은 `/pipeline/run` 데모 파이프라인과 `/pipeline/sync` Repo RAG P0 골격까지 들어와 있다. 다음 단계는 in-memory 저장소를 Postgres/pgvector 기반으로 바꾸고, GitHub repo 변경분을 안정적으로 저장/검색/검증하는 흐름을 완성하는 것이다.

이 문서는 Repo RAG 구현 순서의 기준 문서다. 제품 원칙은 `00-product-plan.md`, 시스템 큰 그림은 `04-system-architecture.md`, AI/RAG 원칙은 `11-ai-agent-rag-plan.md`, 현재 백엔드 클래스 구조는 `15-current-class-uml.md`를 함께 본다.

## 현재 상태 정리

- 제품 방향: `RepoPilot`
  - GitHub 로그인 후 repo를 선택하면 해당 repo의 branch, docs, code, issue, PR, commit을 자동 분석한다.
  - 핵심 차별점은 코드-문서 정합성 검증이다.
  - AI는 직접 write하지 않고 citation과 approval이 있는 proposal만 만든다.

- 현재 구현 흐름
  - `/pipeline/run`: 즉시 실행되는 데모 파이프라인
  - `/pipeline/sync`: Repo RAG 증분 sync 골격
  - `repository_url > repository_path > files` 우선순위로 repo snapshot 생성
  - GitHub HTTPS repo URL 허용, 테스트/개발용 `file://`는 env gate로 허용
  - sync job, stage event, diff, chunk, soft delete, cleanup 골격 존재
  - 현재 store는 in-memory, Postgres DDL은 준비됨

- 연결될 지식 소스
  - 선택한 GitHub repo의 README/docs Markdown
  - 선택한 GitHub repo의 default branch, open PR branch, 최근 active branch
  - GitHub issues, PRs, commits
  - repo 내부 코드와 문서
  - 현재 저장소에서는 `docs/woonyong/*`가 seed/demo 지식 소스 역할을 한다.

## Key Changes

### 1. Repo RAG 저장소를 Postgres로 전환

- `InMemoryRepoRagStore`와 같은 책임을 유지하되 SQLAlchemy/Postgres 구현체를 추가한다.
- source of truth는 Postgres로 둔다.
- `repository_connections`, `branch_snapshots`, `source_files`, `source_chunks`, `retrieval_chunks`, `sync_jobs`, `sync_events`, `findings`, `proposals` DDL을 실제 runtime repository와 맞춘다.
- active row 정책을 유지한다.
  - active file/chunk만 RAG 조회 대상
  - 삭제/수정된 file/chunk는 `is_active=false`, `deleted_at` 기록
  - cleanup worker가 retention 이후 hard delete

완료 기준:

- `/pipeline/sync` 실행 후 job, event, snapshot, file, chunk row가 Postgres에 저장된다.
- 같은 repo/branch active job은 dedupe된다.
- added/modified/deleted/unchanged diff가 DB 기준으로 재현된다.
- repo 연결 해제 시 관련 source/chunk/vector/finding/proposal이 검색에서 제외된다.

### 2. Repo Fetch/Cache를 안정화

- 현재 임시 clone 방식은 유지 가능한 MVP지만, 다음 단계에서는 persistent cache/fetch로 전환한다.
- 기본 구조:
  - GitHub URL allowlist 유지
  - git subprocess timeout 유지
  - repo/branch lock 유지
  - cache directory는 Docker named volume로 관리
- 권장 구현:
  - public repo는 HTTPS clone/fetch
  - private repo와 GitHub App token은 P1로 분리
  - P0에서는 cache 재사용과 branch/commit snapshot 안정성을 우선

완료 기준:

- 같은 public GitHub repo를 반복 sync할 때 매번 full clone하지 않는다.
- branch, commit_sha, file_count가 stage event와 snapshot에 남는다.
- Docker 환경에서 host path mount 없이 `repository_url` sync가 동작한다.

### 3. Chunking과 Retrieval Metadata 확장

- 문서 chunk:
  - Markdown heading 기준
  - frontmatter/type/status/assignee/tags 유지
  - source path와 heading citation 저장
- code chunk:
  - P0는 file-level chunk
  - P1에서 symbol/line range/tree-sitter 확장
- 팀원별 분석 문서:
  - branch, author, commit, 날짜, 구현 주제 metadata를 chunk에 붙인다.
  - 예: `minjeong`, `gain`, `chanbin`, `woohyun` 문서는 "구현 히스토리 지식"으로 인덱싱한다.

완료 기준:

- 사용자가 "민정 브랜치 Board 구현 흐름 알려줘"처럼 물으면 문서 citation과 함께 답할 수 있다.
- 사용자가 "이 코드와 연결된 문서가 뭐야?"를 물으면 code path 기반 retrieval이 가능하다.

### 4. Embedding + pgvector 저장

- embedding provider interface를 둔다.
  - 기본: local/stub embedding
  - 선택: OpenAI embedding
- `chunk_hash` 기준으로 변경된 chunk만 embedding한다.
- active chunk만 검색 대상이다.
- 삭제/수정 chunk의 vector는 soft delete 상태를 반영해 검색에서 제외한다.

완료 기준:

- 동일 snapshot 재실행 시 embedding row가 중복 생성되지 않는다.
- modified file은 old chunk 비활성화 + new chunk embedding 생성으로 처리된다.
- deleted file의 chunk는 검색 결과에서 즉시 빠진다.

### 5. API와 Frontend Sync 상태 노출

- API
  - `GET /auth/github/login`: GitHub OAuth 시작
  - `GET /auth/github/callback`: OAuth code 교환, GitHub token 저장, RepoPilot session cookie 발급
  - `GET /auth/me`: 현재 RepoPilot 사용자 조회
  - `POST /auth/logout`: session revoke
  - `GET /github/repositories`: 로그인 사용자가 접근 가능한 repo 목록 조회
  - `POST /pipeline/sync`: repo sync job 생성 및 현재는 inline 실행
  - 이후 `POST /repository-connections/{id}/sync`: job enqueue만 수행
  - `GET /repository-connections/{id}/permission`: GitHub token/scope/repo permission 상태 조회
  - `GET /sync-jobs/{id}`: job status, stage events, counts 조회
  - `GET /repository-connections/{id}/chunks`: active chunk 조회
  - `GET /repository-connections/{id}/findings`: stale/partial/missing finding 조회
  - `GET /repository-connections/{id}/proposals`: 승인 대기 action 조회
- Frontend
  - GitHub OAuth login
  - 접근 가능한 repo 목록
  - repo 선택과 분석 시작 버튼
  - 최신 commit, file count, chunk count, job status, stage event 표시
  - finding/proposal dashboard 표시
  - 실패 시 400/clone/validation 메시지 표시

완료 기준:

- 화면에서 GitHub 로그인 후 repo를 선택하고 sync 결과를 확인할 수 있다.
- sync history와 stage event가 읽힌다.
- 권한 문제가 있으면 `needs_reauth`, `insufficient_scope`, `sso_required`, `repo_access_lost`, `rate_limited` 상태와 required action을 보여준다.
- stale/inactive chunk가 화면과 retrieval에 섞이지 않는다.
- 승인된 proposal이 GitHub API나 문서 patch로 실행된 뒤 재-sync로 검증된다.

### 6. Agent Proposal로 연결

- RAG 검색은 바로 write하지 않고 proposal 생성으로 이어진다.
- P1 기능:
  - related code suggestion
  - stale doc-code link detection
  - issue draft suggestion
  - doc patch proposal
- proposal은 evidence, confidence, target, proposed_change, approval status를 가진다.

완료 기준:

- AI 응답은 citation을 포함한다.
- 문서 수정/issue 생성/GitHub write는 approval 전 실행되지 않는다.

## Test Plan

- Repo sync
  - `repository_url > repository_path > files` 우선순위
  - GitHub HTTPS allowlist
  - invalid URL 400
  - git timeout
  - tracked UTF-8 file만 수집
  - binary, non-UTF-8, large file 제외

- Diff/soft delete
  - added file creates active file/chunk
  - modified file retires old file/chunk and creates new active file/chunk
  - deleted file retires active file/chunk without creating new chunk
  - unchanged file does not duplicate chunk
  - repeated sync is idempotent

- Job/event
  - manual/schedule/webhook producer가 같은 queue contract 사용
  - same repo/branch active job dedupe
  - job status transition 기록
  - stage event append-only 기록
  - failure records error and releases lock

- DB/vector
  - Postgres repository implementation matches in-memory behavior
  - active-only query excludes deleted rows
  - cleanup hard deletes only inactive rows past retention
  - changed chunk만 embedding
  - pgvector smoke search returns active citation

- API/UI
  - `/pipeline/sync` returns job, repository, changes, active_chunks, events
  - sync status endpoint returns persisted state
  - frontend displays success/failure/status/counts
  - stale/deleted data is not displayed as active

## Implementation Order

1. GitHub OAuth login, server-side session cookie, repo 목록 조회
2. GitHub token 암호화 저장과 permission health check
3. `RepositoryConnection` 중심 Postgres store interface와 SQLAlchemy 구현
4. `/pipeline/sync`를 Postgres store에 연결
5. default/open PR/recent active branch sync 정책 추가
6. persistent repo cache/fetch 추가
7. source chunk metadata 확장
8. embedding provider + pgvector 저장
9. sync job polling worker 전환
10. repo analysis dashboard UI 추가
11. finding/proposal 생성과 approval flow 추가
12. related-code/stale-link proposal 기능으로 확장

## Assumptions

- P0는 GitHub OAuth로 사용자가 접근 가능한 repo를 선택하는 흐름을 기준으로 한다.
- private repo는 OAuth scope 또는 후속 GitHub App 설치 권한 범위 안에서 다룬다.
- P0의 code chunk는 file-level로 시작하고, symbol-level parsing은 P1에서 tree-sitter로 확장한다.
- 현재 `/pipeline/sync`는 inline worker 실행이지만, 최종 구조는 job enqueue + worker polling이다.
- `docs/woonyong/*` 문서는 현재 저장소에서 seed/demo knowledge source로 사용한다.
