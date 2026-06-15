# 백엔드 핸드오프 프롬프트 (RepoLM 팀 공유 모델 지원)

> 아래 블록을 백엔드 작업 중인 Claude에게 그대로 전달하세요.

---

## 컨텍스트

RepoLM은 팀이 GitHub 저장소·문서를 인덱싱해 **근거 기반 Q&A + 문서↔코드 어긋남 제안**을 하는
도구다. 백엔드는 FastAPI + 헥사고날(포트/어댑터) + 레이어드. 저장소는 in-memory와 Postgres(SQL)
두 구현을 `settings.uses_postgres`(=`POSTGRES_DATABASE_URL` 유무)로 선택하고, FastAPI Depends로
조립한다. 테스트는 pytest(현재 128 passed / 6 skipped: SQL은 PG-가드).

**이미 동작하는 것**

- `app/repo_rag`: repo sync(git clone) → 심볼/마크다운 청킹 → 임베딩 → pgvector 하이브리드 검색.
  `POST /pipeline/sync`, `GET /pipeline/sync/{job_id}`, `POST /pipeline/search`. DB 폴링 워커(poller).
- `app/proposals`: 제안 = 상태머신(PENDING→APPROVED/REJECTED), in-memory+SQL.
  `POST /pipeline/proposals`(생성), `GET /pipeline/proposals[?status=]`, `.../{id}/approve|reject`.
- `app/github`: 웹훅 서명검증·수신(`POST /github/webhook`), 제안→이슈 코멘트 발행
  (`POST /github/proposals/{id}/publish`, 세션 사용자 OAuth 토큰 사용).
- `app/auth`: GitHub OAuth 로그인(`/auth/github/login|callback`), 세션 JWT(HS256, httponly 쿠키
  `rp_session`), `GET /auth/me`, GitHub access token 저장(in-memory+SQL). 의존성
  `get_current_claims`(세션→SessionClaims{user_id, login}), `get_github_token_store`.

**제약**

- 헥사고날 유지: 도메인 포트 + in-memory/SQL 어댑터. `dependencies.py`가 settings로 선택.
- 각 작업마다 오프라인 단위 테스트 + PG-가드 통합 테스트(`POSTGRES_DATABASE_URL` 있을 때만).
- 새 테이블은 `docker/postgres/init/00N_*.sql`에 번호 순으로. ruff 통과.
- 커밋: 한글 Conventional Commits, 작업 단위 최소화, 각 커밋 테스트 green.
- 설계 기준 문서: `docs/woonyong/team-sharing-model.md`.

## 목표

팀 공유/가시성 모델을 백엔드로 지원한다. 프론트는 별도 작업으로 이 API를 소비한다.

## 작업 (우선순위 순)

### 1. 워크스페이스 / 멤버 / 역할 (기반)

- 도메인: `Workspace(id, name, owner_user_id)`, `Membership(workspace_id, user_id, role)`,
  role ∈ {owner, member, viewer}.
- 세션 사용자 → 소속 워크스페이스+역할 resolve. 의존성 `require_write(workspace)`(owner/member만 통과,
  viewer는 403)로 쓰기 게이트.
- 엔드포인트: `GET /workspaces`(내 워크스페이스 목록), `GET /workspaces/{id}/members`.
- 데모/부트스트랩: 로그인 사용자를 기본 워크스페이스의 owner로 자동 생성해도 됨.

### 2. 소스(저장소) 목록 + 파일 트리

- `GET /pipeline/repositories?workspace_id=` → [{id, name, branch, connected_by, indexed_at,
  file_count, status}]. (repo_rag 저장소에 list_repositories 추가)
- `GET /pipeline/repositories/{id}/files` → 인덱싱된 파일 경로 → 폴더 트리(JSON). "문서만" 필터 쿼리.
- `GET /pipeline/repositories/{id}/files/{path}` → 파일 본문(뷰어용; 스냅샷/청크에서 재구성).
- `POST /pipeline/sync`에 `workspace_id` + `connected_by`(세션 사용자) 기록, **쓰기 역할 체크**.

### 3. 대화 영속화 + 공유 (개인 기본)

- 도메인: `Conversation(id, workspace_id, owner_user_id, title, visibility, created_at)`,
  visibility ∈ {private, team}. `Message(conversation_id, role, content, citations[], created_at)`.
- `POST /conversations`, `GET /conversations`(내 것 + team 공유된 것),
  `GET /conversations/{id}`(owner이거나 team이면 멤버), `POST /conversations/{id}/messages`
  (질문 저장 → 내부적으로 hybrid search 호출 → 답변+citation 저장),
  `POST /conversations/{id}/share`(visibility=team).
- 권한: private는 owner만, team은 워크스페이스 멤버 읽기.

### 4. 보드 = GitHub Issues 읽기 미러 (단방향)

- `GET /board?repo=owner/name&label=RepoLM` → 세션 사용자 OAuth 토큰으로 GitHub Issues 조회(read-only).
  응답: [{number, title, state, author, assignee, labels, updated_at}].
- **쓰기 없음**(SSOT=GitHub). 보드 편집 API 만들지 말 것. 제안 발행은 기존 엔드포인트 유지.

### 5. 작성자(created_by) 노출

- `proposals`·sources(repositories)에 `created_by`(user_id/login)+`created_at` 추가.
  기존 generate/sync에서 세션 사용자 기록. 응답 스키마에 노출.

## 산출 형식

각 작업: 도메인 포트/레코드 → in-memory 어댑터 → SQL 어댑터(+init SQL) → 서비스 → API 라우터/스키마 →
dependencies 배선 → 테스트. 작은 커밋으로. 끝나면 전체 pytest + ruff green 확인.

---
