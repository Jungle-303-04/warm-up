# 백엔드 핸드오프 프롬프트 (RepoLM 팀 공유 모델 지원)

> 아래 블록을 백엔드 작업 중인 Claude에게 그대로 전달하세요.
> 프론트가 이 모양 그대로 소비하므로 **응답 스키마는 계약**입니다. 필드명을 바꾸면 알려주세요.

---

## 컨텍스트

RepoLM은 팀이 GitHub 저장소·문서를 인덱싱해 **근거 기반 Q&A + 문서↔코드 어긋남 제안**을 하는
도구다. 백엔드는 FastAPI + 헥사고날(포트/어댑터) + 레이어드. 저장소는 in-memory와 Postgres(SQL)
두 구현을 `settings.uses_postgres`(=`POSTGRES_DATABASE_URL` 유무)로 선택하고 FastAPI Depends로
조립한다. 테스트는 pytest(현재 128 passed / 6 skipped: SQL은 PG-가드).

**이미 동작하는 것**

- `app/repo_rag`: repo sync(git clone) → 심볼/마크다운 청킹 → 임베딩 → pgvector 하이브리드 검색.
  `POST /pipeline/sync`, `GET /pipeline/sync/{job_id}`, `POST /pipeline/search`. DB 폴링 워커(poller).
- `app/proposals`: 제안 상태머신(PENDING→APPROVED/REJECTED), in-memory+SQL.
  `POST /pipeline/proposals`, `GET /pipeline/proposals[?status=]`, `.../{id}/approve|reject`.
- `app/github`: 웹훅 서명검증·수신(`POST /github/webhook`), 제안→이슈 코멘트 발행
  (`POST /github/proposals/{id}/publish`, 세션 사용자 OAuth 토큰 사용).
- `app/auth`: GitHub OAuth(`/auth/github/login|callback`), 세션 JWT(HS256, httponly 쿠키
  `rp_session`), `GET /auth/me`, GitHub access token 저장(in-memory+SQL). 의존성
  `get_current_claims`(세션→SessionClaims{user_id, login}), `get_github_token_store`.
- `app/pipeline`(에이전트): `LlmProposer` 포트 + `LangGraphProposer`(StateGraph: gather_evidence→draft).
  `llm_provider="none"`이면 휴리스틱 fallback. **답변 생성 그래프는 아직 없음(retrieve까지만).**

**제약**

- 헥사고날 유지: 도메인 포트 + in-memory/SQL 어댑터. `dependencies.py`가 settings로 선택.
- 각 작업마다 오프라인 단위 테스트 + PG-가드 통합 테스트(`POSTGRES_DATABASE_URL` 있을 때만).
- 새 테이블은 `docker/postgres/init/00N_*.sql`에 번호 순으로. ruff 통과.
- 커밋: 한글 Conventional Commits, 작업 단위 최소화, 각 커밋 테스트 green.
- 설계 기준 문서: `docs/woonyong/team-sharing-model.md`(권한·가시성의 진실 공급원).

## 공통 계약 규약 (모든 신규 엔드포인트 공통)

- **인증**: 모든 신규 엔드포인트는 세션 필요. 미인증·만료 → `401`. 권한 부족 → `403`.
- **권한 2축(중요, 혼동 금지)**:
  - **가시성 = GitHub** : 사용자는 자신이 GitHub에서 접근 가능한 repo의 소스/보드만 본다
    (`required_repos ⊆ member.accessible_repos`). `accessible_repos`는 OAuth 토큰으로 조회,
    **4h 캐시 + 로그인 시 갱신**.
  - **쓰기 = 워크스페이스 역할** : 소스 연결·제안 발행·(향후) 태스크 쓰기는 owner/member만.
    viewer는 `403`. 의존성 `require_write(workspace_id)`로 게이트.
  - 즉 "볼 수 있나"는 GitHub, "쓸 수 있나"는 role. 두 축은 독립.
- **작성자 표현 통일**: 어디서나 `author = {login, avatar_url}`. 보드의 GitHub author도 같은 모양으로 매핑.
- **목록 응답 봉투 통일**: `{ "items": [...], "next_cursor": string | null }`. 정렬 기준은 엔드포인트별 명시.
- **시간**: ISO-8601 UTC 문자열(`created_at`, `updated_at`, `indexed_at`).
- **에러 형식**: `{ "detail": "사람이 읽는 메시지", "code": "machine_code" }`(FastAPI 기본 detail 확장).
- **계약 검증**: 완료 시 FastAPI OpenAPI(`/openapi.json`) 공유. 각 엔드포인트 응답 예시는 아래에 명시.

## 작업 (우선순위 순)

### 1. 워크스페이스 / 멤버 / 역할 (쓰기 게이트 기반)

- 도메인: `Workspace(id, name, owner_user_id)`, `Membership(workspace_id, user_id, role)`,
  role ∈ {owner, member, viewer}.
- 세션 사용자 → 소속 워크스페이스+역할 resolve. 의존성 `require_write(workspace_id)`(owner/member 통과,
  viewer는 403). 가시성 게이트 `accessible_repos(user)`(GitHub, 4h 캐시)도 여기서 제공.
- 엔드포인트: `GET /workspaces`(내 워크스페이스), `GET /workspaces/{id}/members`.
- 부트스트랩(데모): 로그인 사용자를 기본 워크스페이스의 owner로 자동 생성하되 **멱등**
  (이미 있으면 재사용, 중복 생성 금지).
- 예시 `GET /workspaces` →
  `{"items":[{"id":"w1","name":"team","role":"owner","member_count":3}],"next_cursor":null}`

### 2. 소스(저장소) 목록 + 파일 트리

- `GET /pipeline/repositories?workspace_id=` → 가시성 필터(accessible_repos) 적용.
  예시: `{"items":[{"id":"r1","name":"team/api","default_branch":"main","branches":["main","develop"],
  "connected_by":{"login":"woonyong","avatar_url":"..."},"indexed_at":"...","file_count":128,
  "status":"ready"}],"next_cursor":null}`
- `GET /pipeline/repositories/{id}/files?branch=&docs_only=` → 인덱싱된 파일 경로의 폴더 트리(JSON).
  **branch 미지정 시 default_branch 기준.** `docs_only=true`면 문서 확장자만.
  예시: `{"branch":"main","tree":[{"type":"dir","name":"docs","children":[{"type":"file",
  "path":"docs/auth.md","kind":"md"}]}]}`
- `GET /pipeline/repositories/{id}/files/{path}?branch=` → 파일 본문(뷰어용).
  **원문 스냅샷에서 반환(청크 재구성 금지 — 손실/순서 문제).** 스냅샷이 없으면 `404`.
  예시: `{"path":"docs/auth.md","branch":"main","kind":"md","content":"# ..."}`
- `POST /pipeline/sync`에 `workspace_id` + `connected_by`(세션) 기록, **require_write 적용.**
- **업로드 소스(D3/D4)**: `POST /pipeline/sources/upload`(md/txt/pdf, multipart) → 텍스트 추출→청킹→임베딩.
  소스 통합 `kind ∈ {repo, md, text, pdf}`. 업로드 가시성=워크스페이스 멤버 전체. require_write.
  목록(`/repositories`)은 `kind` 포함해 레포+업로드를 함께 반환.

### 3. 대화 영속화 + 공유 (개인 기본)

- 도메인: `Conversation(id, workspace_id, owner_user_id, title, visibility, scope_source_ids[],
  created_at)`, visibility ∈ {private, team}. `Message(conversation_id, role, content, citations[],
  created_at)`. **`scope_source_ids`(질의 범위)를 대화에 저장** — 프론트의 "N개 소스 기준" 재현용.
- `POST /conversations`(scope_source_ids 포함), `GET /conversations`(내 것 + team 공유분),
  `GET /conversations/{id}`(owner이거나 team이면 멤버), `POST /conversations/{id}/share`(visibility=team).
- 권한: private는 owner만, team은 워크스페이스 멤버 읽기. **대화 생성은 viewer도 본인 것은 허용**
  (쓰기 게이트는 "공용 자원"인 소스·발행에만 적용; 개인 대화는 예외).
- 예시 `GET /conversations` →
  `{"items":[{"id":"c1","title":"인증 흐름 점검","visibility":"private","scope_source_ids":["r1","r2"],
  "owner":{"login":"woonyong","avatar_url":"..."},"updated_at":"..."}],"next_cursor":null}`

### 3.5 답변 생성 그래프 (채팅 핵심 — 신규)

- `POST /conversations/{id}/messages`(질문 저장) → **답변 LangGraph 호출** → 답변+citations 저장.
- 그래프(LangGraph, 기존 `LlmProposer`와 같은 헥사고날): `retrieve`(hybrid search, scope_source_ids로
  필터) → `pack_context`(상위 청크 패킹) → `answer`(LCEL: prompt|chat_model|parser, citations 포함) →
  `groundedness`(근거 부족하면 **abstain**: "근거를 찾지 못했습니다"). 포트 `AnswerGraph`로 두고
  `llm_provider="none"`이면 retrieve 결과 요약 fallback(오프라인 테스트).
- 응답 예시: `{"message":{"role":"assistant","content":"...","citations":[{"index":1,
  "source_id":"r1","path":"api/auth.py","line":12}]}}`
- **범위(D7)**: 1차 의도 = `lookup`(근거 Q&A) + `locate`(심볼→파일:라인) + `summarize`(스코프 요약).
  consistency/change는 후속. 라우터·의도분류는 langgraph-agent-design.md 참고.
- **planning(D8)**: 일정 제안은 채팅 답변(`kind="schedule"`, 태스크 초안)과 보드 액션(local 태스크 생성) 양쪽.

### 4. 보드 = GitHub 미러 + 로컬 태스크 (D5)

- `GET /board?workspace_id=&label=RepoLM&state=&cursor=` → **두 출처 집계**, item에 `origin`.
  - `origin="github_issue"`: 연결된 **모든 repo**의 GitHub Issues(OAuth 토큰, read-only, 캐시 TTL 4h, 멀티레포).
  - `origin="local"`: RepoLM 로컬 태스크(아래 CRUD). 승인된 제안 → local 태스크 자동 생성.
- 로컬 태스크 쓰기(역할 게이트): `POST /board/tasks`, `PATCH /board/tasks/{id}`(상태/담당자), `DELETE`.
  GitHub 이슈는 편집 불가(미러). GitHub로의 쓰기는 제안 발행 엔드포인트로만.
- 예시 item: `{"origin":"github_issue","repo":"team/api","number":42,"title":"...","state":"open",
  "author":{"login":"...","avatar_url":"..."},"assignees":[...],"labels":["RepoLM"],"updated_at":"..."}`
  / `{"origin":"local","id":"t1","title":"...","status":"todo","due":"2026-06-20","repo":"team/api",
  "author":{"login":"...","avatar_url":"..."}}`

### 5. 작성자(created_by) 노출

- `proposals`·`repositories`에 `created_by`(=`author{login,avatar_url}`)+`created_at` 추가.
  기존 generate/sync에서 세션 사용자 기록, 응답 스키마에 노출(공통 author 모양).

## 산출 형식

각 작업: 도메인 포트/레코드 → in-memory 어댑터 → SQL 어댑터(+init SQL) → 서비스 → API 라우터/스키마 →
dependencies 배선 → 테스트(오프라인 + PG-가드). 작은 커밋으로. 끝나면 전체 pytest + ruff green,
그리고 `/openapi.json`을 공유.

---
