# Realtime UI and Collaboration

이 문서는 UI와 협업 경험의 방향을 정의한다. 최신 2주 MVP에서는 문서 draft의 자동저장과 최소 동시 편집을 포함한다. 다만 마우스 포인터, 화면 follow mode, Figma식 presence, Notion식 block editor는 제외한다. 첫 버전은 `Home`, `Docs`, `Tasks`, `Calendar`, `AI`, `Approvals`에 집중한다.

## UI 목표

이 제품은 개발팀용 운영 도구이므로 첫 화면은 랜딩이 아니라 실제 작업 화면이어야 한다.

핵심 화면:

- Workspace Home
- Docs
- Code
- Tasks
- Calendar
- Meetings
- Wiki
- GitHub
- AI
- Knowledge Map: P1 이후

## Workspace Home

첫 화면은 오늘 해야 할 일을 보여준다.

```text
┌─────────────────────────────────────────────────────────────┐
│ Sidebar │ Topbar: Repo / Branch / Search / Sync / User      │
├─────────┼───────────────────────────────────────────────────┤
│ Home    │ Today                                             │
│ Docs    │ - meeting 10:00                                   │
│ Code    │ - API doc review due                              │
│ Tasks   │                                                   │
│ GitHub  │ My Work                    AI Panel               │
│ AI      │ - #42 auth API             Ask repo/project       │
│         │ - docs/specs/api.md        Approvals: 2           │
│         │                                                   │
│         │ Delayed                   Recent Changes          │
│         │ - #31 overdue             - PR #12 merged         │
└─────────┴───────────────────────────────────────────────────┘
```

## 문서 편집 화면

Markdown editor는 세 패널 구조를 권장한다.

```text
Document tree | Markdown editor / preview | AI context panel
```

필수 기능:

- Markdown 작성
- frontmatter 폼 편집
- type selector
- type-specific properties
- preview
- outline
- autosave status
- last published status
- active editor 표시
- linked GitHub issues
- related files
- AI "이 문서로 일감 만들기"

## 코드 뷰어

장기적으로는 GitHub 소스코드까지 편집할 수 있어야 한다. 2주 MVP에서는 읽기, 검색, AI patch proposal까지만 한다.

MVP 범위:

- repo file tree
- file open
- syntax highlighting
- search
- read-only default
- diff preview
- AI patch proposal

MVP 제외:

- 앱 안 코드 직접 편집
- code file 공동 편집
- branch/commit workflow for source code

## 실시간 협업 상태

2주 MVP에 포함할 최소 협업 상태:

- 온라인 사용자
- 현재 편집 중인 문서
- 타이핑 상태
- 마지막 저장 시각
- 마지막 publish 시각

2주 MVP에서 제외할 고급 presence:

- 마우스 포인터
- 화면 follow mode
- 보드 카드 hover/drag 실시간 공유
- 캘린더 viewport 공유
- 화려한 cursor animation

기술 후보:

- Yjs + CodeMirror for Markdown
- Hocuspocus or y-websocket for collaboration server
- awareness protocol for active editor/typing status

저장 원칙:

```text
실시간 편집 내용 -> Draft DB
안정적인 snapshot -> workspace repo 자동 publish
code repo 변경 -> PR proposal
```

## 화면 동기화

사용자가 말한 "계정별로 실시간 동기화 몇 화면으로 보여줌"은 장기적으로 다음 기능으로 구체화한다. 2주 MVP에서는 문서 편집 세션의 active editor와 저장 상태까지만 구현한다.

### Follow Mode

한 사용자가 발표자 역할이 되면 다른 사용자가 같은 문서/위치/선택 영역을 따라간다.

### Shared View State

팀원이 어떤 보드 필터, 캘린더 범위, 문서 heading을 보고 있는지 공유한다.

### Cursor Telemetry

문서에서는 커서, 코드에서는 파일/라인, 보드에서는 카드 hover/drag를 보여준다.

## 보드 뷰

GitHub Project/Trello 스타일 보드.

컬럼:

```text
Backlog | Ready | In Progress | Review | Done
```

카드에 표시:

- title
- GitHub issue number
- assignee avatar
- due date
- priority
- labels
- linked document
- evidence score
- blocker indicator

기능:

- drag and drop status update
- filter by owner, label, milestone, due date
- group by assignee/status/priority
- AI issue planning button
- GitHub Project field sync

## 캘린더/스케줄 뷰

표시 대상:

- tasks with due/start
- meetings
- milestones
- PR review deadlines
- planned development slots
- sprint boundaries

뷰:

- month
- week
- day
- agenda list
- timeline

필터:

- assignee
- status
- repo
- milestone
- label
- document type
- overdue only

## 회의록 화면

회의록은 작성하면서 바로 액션을 뽑을 수 있어야 한다.

구성:

- agenda
- notes
- decisions
- action items
- related docs/issues
- AI summary

AI 버튼:

- 회의록 요약
- 액션 아이템 생성
- 결정사항 ADR로 변환
- GitHub Issue 후보 생성
- 다음 회의 agenda 생성

## 위키 화면

Wiki는 문서 목록이 아니라 지식 구조를 보여준다.

기능:

- tags
- backlinks
- graph
- recent updates
- orphan docs
- stale docs
- related code files

## Knowledge Map

너굴맵에서 얻은 아이디어를 개발 프로젝트에 맞게 바꾼다.

```text
docs/specs/api.md
  -> src/routes/auth.ts
  -> src/services/auth.ts
  -> tests/auth.test.ts
  -> issue #12
  -> PR #18
```

이 화면은 다음에 유용하다.

- API 문서와 구현 연결 확인
- 문서 없는 코드 찾기
- 이슈만 있고 구현 없는 작업 찾기
- 회의 결정이 반영된 문서/코드 확인

## AI Panel

AI Panel은 모든 화면에서 같은 위치에 둔다.

모드:

- Ask: 질문 답변
- Plan: 일감 분해
- Compare: 문서/코드/일정 비교
- Act: 승인 기반 실행
- Report: 주간/일일 리포트

AI 답변 카드:

- answer
- evidence
- proposed actions
- approval buttons
- tool log
- follow-up suggestions

## 필터 UX

필터는 모든 뷰에서 공통으로 동작해야 한다.

공통 필터:

- `assignee`
- `status`
- `priority`
- `repo`
- `branch`
- `milestone`
- `label`
- `date range`
- `document type`
- `has blocker`
- `has GitHub issue`
- `stale`

## 모바일

MVP는 데스크톱 우선이지만 모바일에서 다음은 가능해야 한다.

- 오늘 할 일 보기
- 회의록 읽기
- 댓글/승인
- AI 질문
- 캘린더 확인

코드 편집과 Knowledge Map은 데스크톱 우선으로 둔다.
