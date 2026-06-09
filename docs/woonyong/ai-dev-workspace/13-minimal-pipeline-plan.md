# 최소 파이프라인 구현 계획

## 목적

이 문서는 RepoPilot MVP를 실제로 움직이는 최소 파이프라인으로 자르기 위한 기준이다.

목표는 모든 기능을 한 번에 만드는 것이 아니다. 먼저 다음 흐름이 끝까지 연결되는지 증명한다.

```text
repo 연결
  -> repo sync
  -> code index
  -> RAG index
  -> agent proposal
  -> human approval
  -> static publish
```

## 원칙

- 프로젝트가 최상위 단위다.
- GitHub는 code, issue, PR, permission의 원본이다.
- PostgreSQL은 app state의 원본이다.
- pgvector와 Redis는 파생 데이터와 실행 보조 수단이다.
- AI는 직접 상태를 바꾸지 않고 proposal만 만든다.
- 긴 작업은 FastAPI request handler가 아니라 worker가 처리한다.
- 모든 로컬 서비스는 Docker Compose로 실행한다.
- 언어 버전과 반복 명령은 `mise`로 고정한다.

## 로컬 실행 단위

```text
web
React/Next.js workspace UI와 static viewer 시작점

api
FastAPI 기반 project, item, GitHub, code index, proposal, publish API

worker-repo-sync
repo, issue, PR, label, milestone, permission 동기화

worker-code-index
repo file, symbol, commit, code reference 색인

worker-rag
문서, 일감, 이슈, PR, 코드 chunk를 retrieval index로 변환

worker-agent
관련 코드 추천, stale 감지, issue draft, 문서 수정 proposal 생성

worker-publish
읽기 전용 static project archive 생성

postgres
Workspace, Project, WorkspaceItem, View, CodeReference, AgentProposal 저장

redis
queue, cache, presence, worker coordination
```

## 버전 관리

`mise`를 사용한다. `mise`는 언어 버전과 프로젝트 task를 `mise.toml`에 묶어둘 수 있다.

초기 기준:

```text
Node.js 24.x
pnpm 10.x
Python 3.12
uv 0.9.x
PostgreSQL 16 + pgvector
Redis 7
```

Node.js는 2026년 기준 24.x가 Active LTS라서 web runtime 기준으로 둔다.
Python은 FastAPI, pgvector, AI 라이브러리 호환성을 우선해 3.12로 시작한다.

패키지 관리는 다음처럼 나눈다.

```text
Frontend dependencies -> pnpm workspace
Backend dependencies  -> uv + pyproject.toml + uv.lock
Runtime services      -> Docker Compose image tag
Repeated commands     -> mise tasks
```

## 최소 데이터 모델

첫 파이프라인은 아래 테이블만 있으면 된다.

```text
projects
repositories
workspace_items
github_issue_links
code_references
doc_code_links
retrieval_chunks
agent_proposals
publish_snapshots
audit_events
```

`WorkspaceItem`은 wiki, task, meeting, decision, spec, api_doc, schedule, milestone을 하나로 다룬다.

## 구현 순서

### 1. 실행 골격

- `mise.toml`에 Node, pnpm, Python, uv 버전을 고정한다.
- `compose.yaml`에 web, api, worker, postgres, redis를 정의한다.
- `/health`와 `/pipeline` API를 만든다.
- worker는 실제 job 처리 전까지 stage별 heartbeat만 출력한다.

완료 기준:

- `mise run setup`이 의존성을 설치한다.
- `mise run compose:config`가 성공한다.
- `mise run compose:up`으로 서비스가 올라간다.
- `http://localhost:3000`과 `http://localhost:8000/health`가 응답한다.

### 2. Project와 Repository 연결

- project CRUD를 만든다.
- GitHub App installation 정보를 저장한다.
- repository attachment를 만든다.
- repo role을 frontend, backend, infra, docs, other 중 하나로 둔다.

완료 기준:

- project 하나가 여러 repo를 가질 수 있다.
- repo별 permission 상태를 저장할 수 있다.
- GitHub token과 secret은 DB에 평문으로 저장하지 않는다.

### 3. GitHub Sync

- issue, PR, label, milestone을 가져온다.
- GitHub webhook 이벤트를 받아 sync job을 큐에 넣는다.
- task와 GitHub issue link를 저장한다.

완료 기준:

- GitHub issue를 WorkspaceItem task와 연결할 수 있다.
- 승인 전 write action은 실행되지 않는다.
- sync 실패는 재시도 가능해야 한다.

### 4. Code Index

- repo snapshot을 clone/fetch한다.
- generated file, secret file, vendor output을 제외한다.
- file path, symbol, line range, commit SHA를 저장한다.
- tree-sitter를 우선하고 언어별 fallback parser를 둔다.

완료 기준:

- 문서가 code reference를 file/symbol 단위로 가질 수 있다.
- GitHub permalink와 optional local VS Code URI를 만들 수 있다.

### 5. RAG Index

- Markdown/MDX page를 heading 기준으로 chunk한다.
- issue, PR, comment는 title/body/comment 단위로 chunk한다.
- code는 file/symbol 단위로 chunk한다.
- 모든 chunk에 project, repo, visibility, permission metadata를 붙인다.

완료 기준:

- retrieval 전에 permission filter가 적용된다.
- citation에 item, issue, code path, commit을 남길 수 있다.

### 6. Agent Proposal

- `search_docs`, `search_code`, `get_item`, `get_issue` internal tool을 만든다.
- `propose_code_link`, `check_code_link_status`, `propose_issue`, `propose_doc_patch`를 만든다.
- proposal은 evidence, confidence, proposed change, approval state를 가진다.

완료 기준:

- AI는 직접 GitHub나 문서를 수정하지 않는다.
- 관련 코드 추천은 승인 전 `suggested` 상태다.
- stale 감지는 `verified`, `stale`, `broken` 전이를 만든다.

### 7. Static Publish

- publish 가능한 item과 view만 snapshot에 포함한다.
- private page, secret, pending proposal, 권한 없는 repo content는 제외한다.
- page tree, search index, filter index, code-link status를 생성한다.

완료 기준:

- app server 없이 읽히는 정적 산출물이 생성된다.
- public viewer는 편집 기능을 갖지 않는다.
- stale/verified/broken/suggested 상태가 읽기 전용으로 표시된다.

## MVP 테스트

P0 테스트는 기능보다 경계를 검증한다.

```text
permission filtering
item type/property behavior
GitHub issue proposal creation
code-doc link status transition
static publish visibility
RAG retrieval permission boundary
```

첫 자동 테스트는 아래부터 만든다.

- `/health` 응답
- `/pipeline` stage 목록
- worker kind validation
- publish visibility rule
- retrieval permission filter
- proposal approval state transition

## 현재 저장소에 추가한 실행 계약

현재 저장소는 제품 코드가 아니라 문서 중심 워크스페이스였기 때문에, 이번 단계에서는 최소 실행 골격만 추가한다.

```text
compose.yaml
.mise.toml
.env.example
apps/web
backend
docker/postgres/init
```

이 골격은 제품 구현이 아니라 파이프라인을 붙일 자리다.
다음 단계부터는 각 worker 안의 placeholder를 실제 use case로 교체한다.
