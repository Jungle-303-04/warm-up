# Two Week Roadmap and Development Items

## 기간 가정

현재 날짜는 2026-06-06 KST다. 사용자가 말한 "2주 이하로 만들어서 5주간 사용" 조건을 기준으로 하면 개발 마감은 2026-06-19가 되어야 한다. 2026-06-20부터 시작되는 약 5주 팀 프로젝트에서 바로 사용 가능한 상태가 목표다.

## 최신 핵심 판단

`RepoPilot MVP`는 GitHub를 대체하는 도구가 아니다. GitHub를 중심에 두되, 코드 레포와 협업 문서를 분리하고, 홈 화면에서 팀 운영을 한눈에 볼 수 있게 만드는 도구다.

2주 MVP의 제품 공식:

```text
RepoPilot MVP =
Home Dashboard
+ GitHub App onboarding
+ Code repo read/index
+ Workspace repo auto publish
+ Draft DB autosave/realtime docs
+ GitHub Issues board/calendar
+ Local RAG/search
+ Approval-based AI actions
+ Installable PWA
```

## 2주 MVP 성공 기준

1. GitHub App 설치 후 code repo를 연결할 수 있다.
2. workspace repo가 자동 생성되거나 연결된다.
3. Home에서 오늘 일정, 내 일감, 지연/막힘, 최근 문서, AI 알림, 승인 대기를 볼 수 있다.
4. Home에서 일정/일감/회의록/문서/API 문서를 생성할 수 있다.
5. 작성 중인 문서는 Draft DB에 자동저장되고, 조건 만족 시 workspace repo에 자동 publish된다.
6. GitHub Issues를 보드/캘린더/필터로 볼 수 있다.
7. repo/docs/issues를 근거로 AI가 답변하고 issue/doc/action proposal을 만든다.
8. code repo 변경은 직접 push가 아니라 PR proposal로만 제안된다.
9. 웹앱은 PWA로 설치 가능해야 하며, Mac/Windows 앱 패키지는 같은 frontend를 Tauri shell로 감싸는 확장 경로를 둔다.

## 반드시 줄일 범위

| 원래 아이디어 | 2주 MVP 결정 |
|---|---|
| Notion 같은 모든 DB/view | `Workspace Item` + type별 속성 + Home/Board/Calendar/Docs |
| Figma식 마우스/화면 follow | 제외. 현재 접속자와 편집 중 표시만 |
| Google Docs 수준 rich text | 제외. Markdown editor + preview |
| 실시간 공동 편집 전체 | 문서 draft 동시 편집과 autosave만 |
| 코드 레포에 문서/회의록 저장 | 제외. workspace repo 분리 |
| code repo 자동 commit | 금지. PR proposal만 |
| GitHub Projects v2 완전 sync | 제외. GitHub Issues/labels/due convention 우선 |
| 다중 repo 전체 graph/RAG | code repo 1개 + optional linked repo allowlist |
| 완전한 MCP 플랫폼 | 내부 action tools 먼저 |
| 자동 자율 에이전트 | approval-based proposal agent만 |
| 별도 네이티브 앱 | 제외. Web/PWA 우선, 필요 시 Tauri wrapper |
| LangChain/LangGraph 전면 도입 | 제외. 내부 tool registry와 approval policy 먼저 |

## 2주 MVP 화면

### 1. Home

가장 중요한 화면이다.

보여줄 것:

- 오늘 일정
- 내 일감
- 마감 임박
- 지연/막힘
- 최근 회의록
- 최근 결정사항
- 최근 문서
- AI alerts
- 승인 대기
- sync/publish 상태

Home에서 가능한 action:

- 일정 추가
- 일감 추가
- 회의록 작성
- 문서 작성
- API 문서 작성
- AI에게 질문
- AI proposal 승인/거절

### 2. Docs/Editor

기능:

- Markdown editor
- preview
- type selector
- type-specific properties
- autosave status
- last published status
- related issues/files
- AI summary/proposal panel

저장 흐름:

```text
editor update
-> Draft DB autosave
-> optional realtime sync
-> auto publish queue
-> workspace repo commit
```

### 3. Tasks

기능:

- GitHub Issues 목록
- status label 기반 board
- assignee filter
- due date filter
- priority filter
- issue detail
- issue 생성/수정/comment

MVP status labels:

- `status:todo`
- `status:doing`
- `status:blocked`
- `status:review`
- `status:done`

### 4. Calendar

기능:

- schedule item 표시
- meeting item 표시
- issue `Due:` 표시
- 문서 review due 표시
- 담당자/status/type 필터
- overdue 표시

### 5. AI / Approvals

기능:

- repo-aware Q&A
- source citation
- issue split proposal
- close issue proposal
- API doc drift proposal
- meeting action item extraction
- approval log

## 2주 MVP 데이터 원본

| 데이터 | 원본 | 앱 저장 |
|---|---|---|
| 코드 | code repo | RAG DB/cache |
| PR | GitHub PR | local cache |
| 일감 | GitHub Issues | local cache |
| 일정 | Workspace Item 또는 Issue convention | events cache |
| 회의록 | Draft DB -> workspace repo | Markdown + item cache |
| 문서/위키/API 문서 | Draft DB -> workspace repo | Markdown + item cache |
| 개발 히스토리 | workspace repo | Markdown + item cache |
| 실시간 편집 | Draft DB/realtime server | snapshots |
| 검색/RAG | code repo + workspace repo + issues | SQLite FTS/optional embedding |

## 기술 스택

2주 안에는 안정성과 구현 속도가 중요하다.

### 추천 스택

- Frontend: React + TypeScript + Vite
- UI: Tailwind + shadcn/ui 또는 최소 컴포넌트
- Editor: CodeMirror
- Installable app: PWA manifest + service worker
- Desktop wrapper: Tauri optional
- Realtime draft: Yjs + y-websocket 또는 단순 WebSocket patch sync
- Backend: Node.js + Fastify
- DB: Postgres 권장, 데모 단독 실행이면 SQLite 가능
- Queue: DB 기반 queue로 시작
- Search: SQLite FTS5 또는 Postgres full text search
- GitHub: GitHub App + Octokit
- Git: simple-git 또는 git CLI wrapper
- AI: OpenAI Responses API 또는 호환 LLM API
- Agent orchestration: P0는 direct API + internal tool registry, P1에서 LangChain/LangGraph optional

### 2주 MVP에서 피할 스택/기능

- Full MCP server
- LangChain/LangGraph mandatory architecture
- pgvector 운영 최적화
- Redis presence infra
- GitHub Projects GraphQL full sync
- ProseMirror/Tiptap 기반 복잡한 block editor
- code repo 직접 편집/commit
- Electron-first desktop app

## 14일 개발 일정

### Day 1: 프로젝트 skeleton과 인증

개발 항목:

- Vite app
- Fastify API server
- DB schema 초기화
- GitHub OAuth login
- 기본 workspace/membership model

완료 기준:

- 사용자가 로그인할 수 있다.
- workspace를 만들 수 있다.
- 앱 role을 저장할 수 있다.

### Day 2: GitHub App 설치와 code repo 연결

개발 항목:

- GitHub App install callback
- installation id 저장
- 접근 가능한 repo 목록
- code repo 선택
- repo metadata sync

완료 기준:

- GitHub App으로 code repo를 연결한다.
- 권한 부족 상태를 UI에 표시한다.

### Day 3: workspace repo 생성과 초기 템플릿

개발 항목:

- workspace repo 자동 생성
- 기본 docs/.workspace 파일 생성
- 첫 commit/push
- workspace repo clone/cache

완료 기준:

- `team/project-workspace` repo가 생성된다.
- 기본 회의록/위키/API 문서 템플릿이 들어간다.

### Day 4: Home dashboard v1

개발 항목:

- Home layout
- sync status
- today section
- my work section
- recent docs section
- approvals placeholder
- AI alert placeholder

완료 기준:

- 팀원이 접속했을 때 현재 프로젝트 상태를 한 화면에서 본다.

### Day 5: Workspace Item과 Unified Create

개발 항목:

- `workspace_items` table
- type selector
- type-specific properties
- schedule/task/meeting/document/wiki/api_doc 생성
- Home에서 `+ New`

완료 기준:

- 홈에서 일정, 일감, 회의록, 문서를 만들 수 있다.
- 타입을 바꾸면 속성이 바뀐다.

### Day 6: Markdown editor와 Draft DB autosave

개발 항목:

- CodeMirror editor
- Markdown preview
- autosave API
- save status UI
- snapshot table

완료 기준:

- 사용자는 저장 버튼 없이 작성한다.
- 브라우저를 닫았다 열어도 draft가 복구된다.

### Day 7: Realtime draft collaboration

개발 항목:

- Yjs/y-websocket 또는 단순 WebSocket sync
- active editor 표시
- last edit 표시
- basic conflict guard

완료 기준:

- 두 명이 같은 회의록을 열고 동시에 편집할 수 있다.
- 마우스 follow는 없어도 된다.

### Day 8: Auto publish worker

개발 항목:

- publish rule evaluator
- publish_jobs
- repo lock
- Markdown materializer
- git commit/push
- publish status UI

완료 기준:

- 회의록/문서가 조건 만족 시 workspace repo에 자동 commit된다.
- 내용이 같으면 commit하지 않는다.

### Day 9: GitHub Issues import and actions

개발 항목:

- issues import
- labels/assignees parse
- due convention parse
- issue create/comment/status label update
- local cache

완료 기준:

- GitHub Issues가 앱에 표시된다.
- 앱에서 issue를 만들고 comment/status를 바꿀 수 있다.

### Day 10: Board and Calendar

개발 항목:

- board view
- calendar view
- assignee/status/type filters
- overdue/blocked 표시
- schedule item과 GitHub issue event 통합

완료 기준:

- Home/Board/Calendar가 같은 데이터를 일관되게 보여준다.

### Day 11: RAG/search indexing

개발 항목:

- workspace repo indexing
- code repo allowlist indexing
- issues/PR indexing
- chunk table
- FTS search
- citation builder

완료 기준:

- 문서/코드/이슈를 검색할 수 있다.
- AI 답변에 넣을 context pack을 만들 수 있다.

### Day 12: AI panel and issue split agent

개발 항목:

- AI panel
- retrieval prompt builder
- source citation
- issue draft JSON
- approval UI
- GitHub issue create

완료 기준:

- "로그인 기능 일감 나눠줘" 요청에 issue 초안이 나온다.
- 승인하면 GitHub Issues가 생성된다.

### Day 13: Close proposal and API doc drift

개발 항목:

- close issue proposal
- evidence score
- API doc vs route diff
- workspace doc patch proposal
- PR proposal placeholder

완료 기준:

- 완료 후보를 근거와 함께 제안한다.
- API 문서와 구현 차이를 보여준다.

### Day 14: QA, security, rehearsal

개발 항목:

- permission error handling
- webhook signature check
- secret file exclude
- publish conflict handling
- PWA manifest/icons/install flow
- macOS/Windows PWA smoke test
- optional Tauri smoke build
- demo scenario
- onboarding guide

완료 기준:

- 실제 팀 repo로 10분 데모가 가능하다.
- macOS/Windows에서 설치형 앱처럼 실행할 수 있다.
- 2026-06-20부터 팀이 사용할 수 있다.

## P0 개발 항목

| ID | 항목 | 설명 |
|---|---|---|
| P0-01 | GitHub OAuth | 사용자 로그인 |
| P0-02 | GitHub App install | repo 권한 연결 |
| P0-03 | Code repo connect | code repo read/index |
| P0-04 | Workspace repo setup | workspace repo 생성/초기 commit |
| P0-05 | Home dashboard | 일정/일감/문서/AI/승인 요약 |
| P0-06 | Workspace Item | type/properties 기반 공통 게시물 |
| P0-07 | Unified Create | 홈에서 일정/문서/일감 생성 |
| P0-08 | Markdown editor | editor/preview/type properties |
| P0-09 | Draft autosave | DB 자동저장과 복구 |
| P0-10 | Realtime draft | 회의록/문서 동시 편집 최소 구현 |
| P0-11 | Auto publish | workspace repo 자동 commit |
| P0-12 | Issue sync | GitHub Issues import/cache |
| P0-13 | Board/Calendar | status/due/assignee/type view |
| P0-14 | Local search/RAG | docs/code/issues FTS + citations |
| P0-15 | AI proposals | issue split, close proposal, API drift |
| P0-16 | Security/audit | role check, token isolation, audit log |
| P0-17 | PWA install | macOS/Windows에서 브라우저 설치형 앱 |

## P1 개발 항목

5주 프로젝트 중 사용하면서 붙인다.

| ID | 항목 | 설명 |
|---|---|---|
| P1-01 | GitHub Project field sync | Project v2 status/date 일부 동기화 |
| P1-02 | Embedding search | FTS에 semantic search 추가 |
| P1-03 | Linked repo | 참조 repo allowlist indexing |
| P1-04 | Weekly report | issue/PR/docs 기반 주간 리포트 |
| P1-05 | Pull request deep import | changed files와 issue 연결 |
| P1-06 | Saved filters | 개인/팀 필터 저장 |
| P1-07 | Document version view | workspace repo git history 기반 |
| P1-08 | Knowledge Map lite | 문서-이슈-파일 관계도 |
| P1-09 | AI property suggestions | 본문에서 due/assignee/action item 추천 |
| P1-10 | Tauri desktop package | macOS `.dmg`, Windows installer |
| P1-11 | LangGraph workflow | weekly report/API drift 같은 multi-step agent |
| P1-12 | MCP wrapper | 내부 tools를 외부 AI client에 노출 |

## P2 개발 항목

2주 MVP와 5주 사용 기간에는 욕심내지 않는다.

| ID | 항목 | 설명 |
|---|---|---|
| P2-01 | 마우스/커서 presence | Figma식 pointer/follow mode |
| P2-02 | Full MCP server | 외부 MCP client에서 도구 호출 |
| P2-03 | Full GitHub Projects sync | GraphQL 기반 완전 양방향 sync |
| P2-04 | Code edit mode | 앱 안에서 코드 수정/commit/PR |
| P2-05 | Advanced dependency graph | repo 관계도와 영향 분석 |
| P2-06 | Block editor | Notion식 블록 에디터 |
| P2-07 | Native desktop integration | tray, native notifications, global shortcut |
| P2-08 | Custom team agents | 팀별 agent config와 MCP tool policy |

## 5주 사용 운영 계획

### Project Week 1

- kickoff 회의록 자동 생성/자동 publish 확인
- goals/roadmap/specs/API 문서 작성
- issue split agent로 초기 backlog 생성
- GitHub board/calendar 운영 시작

### Project Week 2

- daily dev log 작성
- API doc drift 확인
- close proposal agent로 완료 후보 검증
- Home에서 지연/막힘 점검

### Project Week 3

- PR import 강화 여부 판단
- weekly report 도입
- 팀 필터와 담당자별 일정 정리

### Project Week 4

- 마감 리스크 issue 찾기
- 구현 대비 문서 차이 정리
- 발표/README/API 문서 정리

### Project Week 5

- 최종 dev history 생성
- 프로젝트 회고 회의록 생성
- 완료/미완료 issue 정리
- 최종 산출물 문서화

## 첫 데모 시나리오

1. GitHub App 설치
2. code repo 선택
3. workspace repo 자동 생성
4. Home dashboard 진입
5. Home에서 kickoff 회의록 작성
6. 두 사용자가 동시에 회의록 편집
7. 자동저장 상태 확인
8. 자동 publish 후 workspace repo commit 확인
9. GitHub Issues import
10. 보드/캘린더에서 담당자와 due date 확인
11. AI에게 "로그인 기능 일감 나눠줘" 요청
12. issue 초안 승인 후 생성
13. AI에게 "API 문서와 구현 차이 확인해줘" 요청
14. 문서 patch/PR proposal 확인
15. macOS/Windows에서 PWA 설치형 앱으로 실행

## 최종 제안

2주 안에 만들려면 제품의 정체성을 다음처럼 고정해야 한다.

```text
RepoPilot MVP =
GitHub App + Home + Draft DB autosave + Workspace repo auto publish
+ GitHub Issues + local RAG + approval-based AI proposals + installable PWA
```

이 범위라면 2주 안에 만들 수 있고, 5주 프로젝트 동안 실제로 쓸 수 있다. 반대로 code repo 직접 편집, 완전한 GitHub Projects sync, Figma식 presence, Notion식 block editor까지 넣으면 도구를 쓰기 전에 도구 개발 자체가 프로젝트가 된다.
