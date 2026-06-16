# 시스템 아키텍처

## 요약

RepoLM은 GitHub repo 연결을 시작점으로 하는 web-first 애플리케이션이다. 사용자는 GitHub OAuth로 로그인해 repo를 선택하고, RepoLM은 branch, docs, code, issue, PR, commit을 자동 분석해 repo dashboard와 approval-based proposal을 제공한다.

Repo RAG의 구체적인 구현 순서와 현재 P0 상태는
`16-repo-rag-implementation-plan.md`를 기준으로 한다. 현재 `/pipeline/sync`는
in-memory store와 inline worker로 동작하는 골격이며, 다음 단계에서
Postgres store와 worker polling 구조로 전환한다.

```text
React/Next.js App
├── Repo Dashboard
├── Static Viewer
└── Admin/Settings

FastAPI Backend
├── Auth and Permissions
├── Repository Connection API
├── GitHub Integration
├── Code Index API
├── AI Proposal API
└── Publish API

Workers
├── GitHub sync
├── Code indexing
├── RAG indexing
├── Static publish
└── AI proposal execution

Storage
├── PostgreSQL
├── pgvector
├── Redis
├── Object storage
└── GitHub repositories
```

## Repository 모델

MVP에서 `RepositoryConnection`은 사용자가 선택한 GitHub repo 하나를 나타낸다. RepoLM은 코드를 소유하지 않고 GitHub OAuth/App 권한으로 읽고 인덱싱한다. 여러 repo를 하나로 묶는 `ProjectGroup`은 후속 확장으로 둔다.

아카이브 산출물은 별도로 관리한다.

```text
GitHub repo     -> code, docs, issues, PRs, commits
app DB          -> source state, findings, proposals, approval log
vector DB       -> active source chunk retrieval
static export   -> public 또는 team archive
```

초기 기획의 workspace/project 아이디어는 repo 묶음과 export target으로 남긴다. MVP에서 사용자는 별도 project를 만들지 않고 repo 선택으로 시작한다.

## 핵심 서비스

### App API

- project CRUD
- item CRUD
- view와 filter
- permission check
- GitHub issue action
- AI proposal review/approval

### Realtime Service

- document presence
- cursor/selection state
- collaborative draft editing
- conflict-safe document update

CRDT 로직을 직접 만들지 말고 Yjs/Hocuspocus 또는 Liveblocks를 사용한다.

### GitHub Sync Worker

- issue, PR, label, milestone 가져오기
- webhook 처리
- 연결된 issue metadata 갱신
- permission state 갱신

### Code Index Worker

- repo snapshot clone/fetch
- file과 symbol parsing
- code chunk 생성
- file/symbol metadata 갱신
- link drift 감지

### RAG Index Worker

- Markdown/MDX page indexing
- issue, PR, comment, meeting indexing
- code chunk indexing
- retrieval 전 permission metadata 적용

### Publish Worker

- publishable item과 view 수집
- static HTML/JS/CSS render
- search/filter index 생성
- 설정된 hosting target에 배포

## 데이터 흐름: 코드-문서 링크

```text
사용자가 문서를 작성
        ↓
AI가 관련 코드를 추천
        ↓
사용자가 링크를 승인
        ↓
DocCodeLink가 file/symbol/commit 저장
        ↓
GitHub webhook으로 repo 변경 감지
        ↓
Code index worker가 link 재검사
        ↓
상태가 verified/stale/broken으로 변경
        ↓
문서와 static viewer에 색상 상태 표시
```

## 데이터 흐름: 회의록에서 이슈 생성

```text
회의록 작성
        ↓
AI가 action item 추출
        ↓
task draft 생성
        ↓
사용자가 GitHub issue 생성을 승인
        ↓
GitHub issue 생성
        ↓
workspace task와 issue 연결
```

## 권한 경계

모든 repo-aware action은 다음을 확인해야 한다.

1. App workspace role
2. GitHub installation access
3. User repository permission
4. Item visibility
5. Publish visibility

Permission filtering은 RAG retrieval과 static publishing 전에 실행되어야 한다.

## MVP 스택

- Frontend: React 또는 Next.js
- Editor: Tiptap/ProseMirror
- Realtime: Yjs/Hocuspocus 또는 Liveblocks
- Backend: FastAPI
- DB: PostgreSQL + pgvector
- Queue: Redis + worker process
- Parsing: tree-sitter 우선, 언어별 regex/AST fallback
- Integration: GitHub App
- Hosting: web app + static export target

## 아키텍처 제약

- 긴 작업은 HTTP request handler 안에서 실행하지 않는다.
- 현재 `/pipeline/sync`의 inline worker는 P0 검증용이며 최종 구조는 job enqueue와 worker polling이다.
- Vector index는 재생성 가능한 파생 데이터이며 source of truth가 아니다.
- AI proposal은 승인 없이 되돌리기 어려운 write를 실행하지 않는다.
- Static viewer는 private repo metadata를 노출하지 않는다.
- Code repo write는 미래 범위이며 PR을 통해서만 다룬다.
