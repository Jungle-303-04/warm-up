# Product Requirements

## 문제 정의

팀 프로젝트에서 정보는 빠르게 흩어진다.

- 코드는 GitHub에 있다.
- 문서는 Notion, Google Docs, README, 개인 메모에 나뉜다.
- 일정은 Google Calendar, Notion Calendar, GitHub Milestone에 흩어진다.
- 일감은 GitHub Issue, Project board, Trello, 채팅에 섞인다.
- 회의록과 결정사항은 나중에 찾기 어렵다.
- AI에게 물어볼 때마다 필요한 맥락을 사람이 다시 붙여넣는다.

이 제품은 이 분산을 줄이기 위해 code repo, workspace repo, GitHub Issues, Draft DB를 분리해 사용한다. UI는 Notion처럼 쉽게 보이되, 2주 MVP에서는 Home dashboard, Markdown 기반 문서, GitHub Issues 기반 일감, 자동저장/자동 publish, 로컬 검색/RAG DB로 정리한다.

## 목표 사용자

- 2~8명 규모의 개발팀
- GitHub 저장소를 쓰는 팀
- 5주 내외의 집중 프로젝트를 진행하는 팀
- 문서화와 일정관리가 자주 누락되는 팀
- AI를 단순 질문 답변보다 프로젝트 운영 보조자로 쓰고 싶은 팀

## 2주 MVP 목표

1. GitHub 프로젝트와 Git repo 문서를 쉽게 관리한다.
2. code repo와 workspace repo를 분리해 코드 히스토리와 협업 문서 히스토리가 섞이지 않게 한다.
3. 저장소를 연결하면 자동으로 로컬 DB와 RAG 인덱스가 생성된다.
4. 홈에서 일정/일감/회의록/문서/위키/API 문서를 한눈에 보고 등록할 수 있다.
5. Markdown 문서를 작성하면 일정/상태/담당자/이슈 링크가 구조화된다.
6. Draft DB에 자동저장하고, 안정적인 시점에 workspace repo로 자동 publish한다.
7. GitHub Issues를 보드, 캘린더, 테이블, 담당자 필터로 보여준다.
8. AI가 현재 일정, 구현 코드, 문서, GitHub Issue를 비교하고 액션 초안을 제안한다.
9. 사용자가 승인하면 AI가 GitHub Issue 상태를 변경하거나 문서 patch/PR 초안을 만든다.
10. 웹앱을 macOS/Windows에서 설치형 앱처럼 사용할 수 있게 한다.

## 장기 제품 목표

- 팀원의 마우스, 커서, 선택 영역, 현재 화면을 실시간으로 볼 수 있다.
- GitHub Projects v2 custom fields를 완전 양방향 동기화한다.
- linked repo 전체를 Knowledge Map과 semantic RAG로 연결한다.
- 앱 안에서 코드 편집, branch 생성, PR 생성까지 처리한다.
- 내부 action 함수를 MCP server로 감싸 외부 AI client에서도 사용할 수 있게 한다.

## 하지 않을 것

- Notion 전체 블록 에디터 복제
- Figma 수준의 디자인 툴 복제
- Google Docs 수준의 모든 문서 서식 지원
- GitHub 전체 웹 UI 복제
- 사용자의 승인 없이 외부 시스템 변경
- code repo main branch 직접 push
- Draft DB의 모든 변경을 Git commit으로 남기기
- 모든 레포 파일을 무조건 벡터화
- 2주 MVP에서 GitHub Projects v2 전체 복제
- 실시간 협업과 Git commit을 같은 저장 이벤트로 혼합

## 핵심 사용자 시나리오

### 저장소 연결과 자동 세팅

사용자는 "GitHub로 시작하기"를 누르고 GitHub App을 설치한 뒤 code repo를 선택한다.

시스템은 다음을 수행한다.

1. code repo 접근 권한 확인
2. workspace repo 자동 생성 또는 기존 workspace repo 연결
3. 기본 문서 폴더, 템플릿, labels, issue convention 생성
4. code repo의 README/source tree/tests/API route 후보 스캔
5. GitHub Issues/PRs/Milestones 동기화
6. 로컬 DB에 파일/문서/이슈/커밋 메타데이터 저장
7. RAG 인덱스 생성
8. Workspace Home에 상태 요약 표시

### 홈에서 일정/문서/일감 등록

사용자는 홈에서 `+ New`를 누른다.

```text
+ New
  - Schedule
  - Task
  - Meeting Note
  - Document
  - Wiki
  - API Spec
  - Decision
  - Dev Log
```

사용자는 먼저 작성하고 나중에 타입을 바꿀 수 있다. 타입이 바뀌면 필요한 속성과 보이는 화면이 바뀐다.

예시:

```text
Document로 작성 시작
-> type을 Meeting으로 변경
-> 참석자, 회의 시간, 안건, 결정사항, 액션아이템 속성 추가
-> Home Today, Calendar, Meetings에 동시에 표시
-> 자동 publish 시 docs/meetings/YYYY-MM-DD-title.md로 저장
```

### 문서 작성

사용자는 Markdown으로 문서를 작성한다. 사용자가 느끼는 저장은 자동저장이다.

내부 저장 흐름:

```text
타이핑
-> Draft DB 자동저장
-> 실시간 편집 세션에 반영
-> 자동 snapshot 생성
-> 조건 만족 시 workspace repo에 자동 publish commit
```

문서에는 frontmatter가 붙는다.

```md
---
type: spec
status: in_progress
owner: woonyong
assignees: [backend, frontend]
start: 2026-06-20
due: 2026-06-27
github_issues: [42, 43]
tags: [api, auth]
---

# Auth API Spec
```

이 문서는 타입과 속성에 따라 동시에 다음 뷰에 나타난다.

- Docs list
- Calendar due date
- Project timeline
- Related GitHub issues
- RAG context
- AI task planning source

### 자동 publish

사용자는 publish 버튼을 누르지 않아도 된다. 시스템이 문서 타입과 편집 상태를 보고 workspace repo에 자동 commit한다.

자동 publish 조건 예시:

```text
회의록: 회의 종료 시간 이후 + 5분간 편집 없음
위키/API 문서: 마지막 편집 후 10분간 편집 없음
개발 히스토리: 하루 1회 또는 30분 batch
AI action log: 즉시 DB 저장, 10분 단위 batch commit
```

화면에는 다음 상태를 보여준다.

```text
저장됨
Git 기록 대기 중
Git에 기록됨 11:03
충돌 발생
```

### 일정/일감 관리

사용자는 같은 데이터를 다양한 뷰로 본다.

- Board: `Backlog -> Ready -> In Progress -> Review -> Done`
- Calendar: start/due/scheduled_at 기반
- Timeline: 프로젝트/마일스톤 기준
- Table: 담당자, 태그, 상태, GitHub issue 번호 필터
- My Work: 현재 사용자 기준
- Delayed: 마감이 지났고 완료되지 않은 항목

### AI에게 완료 반영 요청

사용자 질문:

```text
현재 일정과 현재 구현된 내용을 비교해서 반영된 내용의 일감을 마감해줘.
```

AI 처리:

1. GitHub Issues/Projects에서 진행 중 일감을 가져온다.
2. 관련 소스 파일, PR, 커밋, 문서를 검색한다.
3. 구현 근거가 충분한 일감을 후보로 분류한다.
4. 각 후보에 "근거 파일/커밋/문서/테스트"를 붙인다.
5. 사용자에게 승인 요청을 보여준다.
6. 승인된 일감만 GitHub Issue/Project 상태를 변경한다.
7. 변경 로그를 개발 히스토리에 남긴다.

### AI에게 작업 분해 요청

사용자 질문:

```text
지금 결제 기능을 만들고 싶은데 어떤 것을 구현하고 일감을 어떻게 나눠야 하지?
```

AI 처리:

1. 현재 문서와 코드 구조를 검색한다.
2. 관련 API, DB schema, UI route, 기존 이슈를 확인한다.
3. 기능을 epic/story/task 단위로 분해한다.
4. 의존성, 예상 기간, 담당 역할, 리스크를 붙인다.
5. GitHub Issue 생성 후보와 Project board 배치안을 만든다.
6. 사용자가 선택하면 이슈를 생성한다.

### API 문서 최신화

사용자 질문:

```text
API 문서와 실제 구현된 API를 비교해서 다르면 실제 구현 기준으로 문서를 최신화해줘.
```

AI 처리:

1. API 문서 Markdown을 파싱한다.
2. 실제 backend route/controller/schema/test를 검색한다.
3. endpoint, method, path, request, response, auth, error code 차이를 표로 만든다.
4. 변경안 patch를 제안한다.
5. 승인 후 Markdown 문서를 수정하고 Git commit 후보를 만든다.

## 필수 기능

| 영역 | 필수 기능 |
|---|---|
| Git | code repo read/index, workspace repo auto publish, PR proposal |
| Markdown | editor, preview, frontmatter, type properties, backlinks |
| 문서 | spec, meeting, wiki, decision, retrospective, api-doc |
| 일감 | task, status board, assignee, priority, due date |
| 일정 | home today, calendar, delayed view, milestone |
| GitHub | app install, issues, labels, milestones, comments, limited project status |
| 실시간 | 문서 draft 자동저장, 동시 편집, 접속자 표시 |
| RAG | local DB, SQLite FTS, optional embeddings, citations |
| MCP | MVP는 내부 action tools. MCP wrapper는 이후 |
| Agent | issue planner, status closer, doc updater, report generator |
| 배포 | web app, installable PWA, optional Tauri desktop wrapper |
| 보안 | GitHub App, app roles, token isolation, secret filtering |
| 감사 | action log, source citations, rollback hints, publish history |

## 품질 기준

- AI 답변은 근거 링크를 포함해야 한다.
- 외부 변경은 승인 전 실행되지 않아야 한다.
- GitHub/토큰 권한은 최소 권한으로 설정해야 한다.
- code repo 변경은 직접 push가 아니라 PR proposal이어야 한다.
- workspace repo write는 서버 bot만 수행해야 한다.
- 자동 publish는 충돌 발생 시 자동 덮어쓰지 않아야 한다.
- desktop/PWA client는 GitHub installation token을 직접 저장하지 않아야 한다.
- 오프라인 또는 API 장애 시에도 로컬 문서 읽기는 가능해야 한다.
- RAG 인덱스 생성 상태와 실패 로그가 UI에 보여야 한다.
- Git 저장 충돌과 AI 변경 충돌은 자동 덮어쓰기보다 명시적 해결을 우선한다.
