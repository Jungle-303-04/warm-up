# 로드맵과 개발 항목

## MVP 목표

첫 빌드는 RepoPilot이 프로젝트 문서, 일감, GitHub issue, code reference를 연결할 수 있음을 증명해야 한다.

## 2주 컷라인

반드시 만든다.

1. Project 생성
2. GitHub App 연결
3. Multi-repo attachment model
4. Page tree와 Markdown/MDX item 본문
5. 공통 item property
6. Table, kanban, calendar view
7. GitHub issue link와 issue draft 생성
8. File/symbol reference용 code indexing
9. Page 위 related code chip
10. Stale/verified/broken/suggested 링크 상태
11. Page tree, search, filter를 가진 static viewer
12. Editor의 기본 authenticated realtime presence

하지 않는다.

- 완전한 Notion database builder
- 완전한 GitHub Projects clone
- 완전한 VS Code extension
- screen sharing/follow mode
- autonomous code write
- 복잡한 multi-repo dependency graph

## 개발 순서

### Day 1-2: 기반

- Project skeleton
- Auth
- PostgreSQL schema
- GitHub App setup
- Repository connection

### Day 3-4: 콘텐츠 모델

- `WorkspaceItem`
- page tree
- Markdown/MDX body
- shared properties
- basic editor

### Day 5-6: 뷰

- table view
- kanban view
- calendar view
- filters
- item type switching

### Day 7-8: GitHub

- issue와 PR 가져오기
- task와 issue 연결
- issue draft 생성
- issue creation approval flow

### Day 9-10: Code Index

- repo files 가져오기
- file/symbol metadata parsing
- code reference 생성
- document에 code reference 연결

### Day 11: Stale Detection

- verified commit 저장
- repo update 처리
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

1. project를 만든다.
2. backend와 frontend repo를 연결한다.
3. auth spec page를 만든다.
4. spec을 auth 관련 file과 연결한다.
5. spec에서 task를 만든다.
6. GitHub issue draft를 만든다.
7. sample repo의 연결된 코드를 변경한다.
8. document status가 yellow/stale로 바뀌는 것을 보여준다.
9. project archive를 publish한다.
10. code link를 GitHub 또는 VS Code로 연다.
