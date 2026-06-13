# 로드맵과 개발 항목

## MVP 목표

첫 빌드는 사용자가 GitHub로 로그인해 repo를 선택하면 RepoPilot이 branch, docs, code, issue, PR, commit을 자동 분석하고 finding/proposal을 보여줄 수 있음을 증명해야 한다.

Repo RAG 구현의 최신 기준은 `16-repo-rag-implementation-plan.md`다. 이 문서는
제품 로드맵을 유지하고, 세부 구현 순서는 16번 문서에 위임한다.

## 2주 컷라인

반드시 만든다.

1. GitHub OAuth 로그인
2. repo 선택과 `RepositoryConnection` 생성
3. default/open PR/recent active branch sync
4. README/docs/code/issue/PR/commit indexing
5. repo analysis dashboard
6. stale document, partial feature, missing test finding
7. GitHub issue/action proposal
8. 승인 후 GitHub API 반영과 재-sync 검증
9. repo disconnect cleanup

하지 않는다.

- 완전한 Notion database builder
- 완전한 GitHub Projects clone
- 완전한 VS Code extension
- screen sharing/follow mode
- autonomous code write
- 복잡한 multi-repo dependency graph

## 개발 순서

### Day 1-2: repo 연결 기반

- GitHub OAuth login
- RepositoryConnection schema
- repo list/select UI
- PostgreSQL schema
- initial sync job

### Day 3-4: source indexing

- branch snapshot
- SourceFile/SourceChunk
- README/docs Markdown chunking
- code file chunking
- issue/PR/commit mirror

### Day 5-6: repo dashboard

- sync status
- branch summaries
- indexed source counts
- finding list
- proposal list

### Day 7-8: GitHub automation

- issue/PR sync
- issue draft proposal
- issue status/comment update proposal
- approval and audit flow

### Day 9-10: Code Index

- repo snapshot sync와 변경분 diff 계산
- active file/chunk 저장
- file-level code chunk 생성
- document와 code reference를 연결할 기반 저장

### Day 11: Stale Detection

- verified commit 저장
- repo update와 soft delete 처리
- link를 verified/stale/broken/suggested로 표시
- 상태 색상 노출

### Day 12: Static Viewer

- static page rendering
- static search/filter index
- read-only task view
- 안전한 public visibility rule

### Day 13: AI Proposals

- repo-aware Q&A
- related-code suggestion
- issue draft suggestion
- evidence/citation output

### Day 14: Polish and Demo

- onboarding path
- permission check
- audit log basics
- demo project data
- deployment rehearsal

## P0 Backlog

- Workspace/project CRUD
- GitHub App install flow
- repo sync worker
- Repo RAG Postgres store 전환
- persistent repo cache/fetch
- item CRUD
- page tree
- table/kanban/calendar
- code reference model
- doc-code link status
- static export
- AI proposal model

## P1 Backlog

- VS Code extension
- 더 풍부한 realtime editor 기능
- comments
- GitHub Projects v2 field sync
- multi-repo knowledge map
- pgvector embedding 저장과 retrieval smoke search
- 더 정교한 code-symbol detection
- scheduled project briefing

## P2 Backlog

- marketplace integration
- MCP server
- self-hosted edition
- advanced analytics
- automated PR proposal flow
- enterprise permission model

## 데모 시나리오

1. GitHub로 로그인한다.
2. `Jungle-303-04/warm-up` repo를 선택한다.
3. default branch와 active branch가 자동 sync된다.
4. `docs/woonyong` 문서와 repo code/issue/commit이 인덱싱된다.
5. dashboard에서 Board API, Recommend API 같은 work area를 본다.
6. partial feature와 stale document finding을 확인한다.
7. GitHub issue draft나 document update proposal을 승인한다.
8. GitHub 반영 후 재-sync로 상태가 갱신되는 것을 보여준다.
