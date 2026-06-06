# Two Week MVP Cutline

## 결론

이 협업툴은 2주 안에 만들 수 있어야 하므로, 첫 버전은 Notion/Figma/Google Docs를 합친 제품이 아니라 GitHub 프로젝트를 더 잘 쓰게 만드는 AI 운영 콘솔이어야 한다.

다만 최신 결정은 다음을 포함한다.

```text
문서 draft의 자동저장과 최소 실시간 공동 편집은 MVP에 포함한다.
마우스 포인터, 화면 follow, Notion식 블록 에디터는 제외한다.
```

## 한 줄 정의

`RepoPilot MVP`는 code repo, workspace repo, GitHub Issues를 연결하고, Home dashboard에서 일정/일감/회의록/문서를 만들고 볼 수 있게 하며, AI가 문서/코드/일감을 근거로 issue 생성, 일정 점검, 문서 최신화를 제안하는 5주 팀 프로젝트용 협업툴이다.

## 반드시 되는 것

### 1. GitHub App 기반 연결

- GitHub OAuth login
- GitHub App installation
- code repo 선택
- repo permission 확인
- installation token은 서버에서만 사용

### 2. Workspace repo 자동 세팅

- workspace repo 생성 또는 연결
- 기본 docs 구조 생성
- `.workspace/` 설정 생성
- 첫 commit 생성
- workspace repo는 서버 bot이 write

### 3. Home dashboard

- 오늘 일정
- 내 일감
- 지연/막힘
- 최근 문서/회의록/결정사항
- AI alerts
- 승인 대기
- sync/publish 상태
- `+ New` 생성 버튼

### 4. Unified Create와 타입 속성

- Schedule
- Task
- Meeting
- Document
- Wiki
- API Doc
- Decision
- Dev Log

사용자는 작성 중 타입을 바꿀 수 있어야 한다. 타입 변경 시 본문은 유지되고 속성/뷰/publish path가 바뀐다.

### 5. Draft DB 자동저장

- Markdown editor
- 자동저장
- snapshot
- 복구
- save status 표시

사용자가 보는 상태:

```text
저장 중...
저장됨
Git 기록 대기 중
Git에 기록됨
충돌 발생
```

### 6. 최소 실시간 공동 편집

- 같은 문서를 두 명이 동시에 열고 편집
- active editor 표시
- 마지막 수정자/시간 표시
- 복구 가능한 draft 저장

제외:

- 마우스 포인터
- follow mode
- 화면 동기화
- 복잡한 presence animation

### 7. 자동 publish

- Draft DB 내용을 조건에 따라 workspace repo로 자동 commit
- publish queue
- repo lock
- content hash check
- conflict handling
- audit log

### 8. 일감/일정 관리

- GitHub Issues import
- labels/assignees/milestone 표시
- status label 기반 board
- issue body의 `Due: YYYY-MM-DD` 파싱
- calendar view
- 담당자/status/type/due 필터
- Home에서 일정/일감 추가

### 9. 로컬 검색/RAG

- workspace docs/code repo/issues chunking
- SQLite FTS 또는 Postgres full text
- 답변 근거 source citation
- "근거 부족" 처리

### 10. AI 액션

- 기능 요청을 GitHub Issue 초안으로 분해
- 구현/문서/issue를 비교해 완료 후보 제안
- API 문서와 구현 route 차이 요약
- 회의록에서 action item 추출
- 사용자가 승인해야 GitHub issue 생성/comment/status 변경
- code repo 변경은 PR proposal만

### 11. 웹앱 설치

- PWA manifest
- app icon
- standalone display
- service worker
- install 안내
- macOS/Windows에서 브라우저 설치형 앱으로 실행

`.dmg`, `.exe`, `.msi` 배포가 꼭 필요하면 같은 web frontend를 Tauri shell로 감싼다. 단, 2주 MVP의 필수 성공 기준은 PWA 설치까지로 둔다.

## 2주 안에는 하지 않는 것

| 제외 항목 | 이유 | 대체 |
|---|---|---|
| 마우스 포인터 동기화 | 구현 비용 대비 MVP 가치 낮음 | active editor 표시 |
| 화면 follow mode | 협업 감성 기능에 가까움 | 같은 문서 열기/링크 공유 |
| Notion식 block editor | 범위 폭발 | Markdown editor |
| 완전한 Notion DB | 스키마 자유도가 큼 | Workspace Item + type properties |
| GitHub Projects v2 완전 sync | GraphQL field 구조가 복잡함 | Issues/labels/due convention |
| code repo 자동 commit | 형상관리 오염과 보안 위험 | PR proposal |
| 앱 안 코드 편집 | 실수 위험과 diff/merge 부담 | code viewer + AI patch proposal |
| 다중 repo 완전 RAG | indexing 범위 관리 어려움 | primary code repo + allowlist |
| 완전한 MCP 서버 | 2주 안에는 wrapper보다 기능이 중요 | 내부 action 함수 |
| Electron-first desktop app | 앱 크기와 패키징 부담 | PWA 우선, 필요 시 Tauri |
| LangChain/LangGraph 전면 도입 | orchestration보다 정책/승인이 중요 | direct LLM API + internal tools |

## 사용자 경험 원칙

1. 팀원은 GitHub를 버리지 않는다.
2. code repo와 workspace repo는 분리한다.
3. 사용자는 저장 버튼을 누르지 않아도 된다.
4. Git에는 안정적인 snapshot만 자동 publish된다.
5. 일정/문서/회의록/일감은 하나의 `Workspace Item`처럼 느껴져야 한다.
6. 사용자는 "어느 DB에 넣을지" 고민하지 않는다.
7. AI는 바로 실행하지 않고 초안을 만든다.
8. 모든 AI 변경은 승인과 로그가 남는다.
9. code repo 변경은 PR로만 간다.
10. 어려운 설정은 setup wizard로 숨긴다.
11. 웹과 데스크톱은 다른 제품이 아니라 같은 frontend를 공유한다.
12. RAG는 P0 필수이고, MCP/LangChain은 P1 이후 확장 수단이다.

## 최소 Workspace Repo 구조

```text
docs/
├── project/
│   ├── goals.md
│   └── roadmap.md
├── specs/
│   ├── architecture.md
│   └── api/
│       └── README.md
├── meetings/
│   └── 2026-06-20-kickoff.md
├── decisions/
│   └── ADR-001-repopilot-workspace.md
├── wiki/
│   └── glossary.md
├── history/
│   └── dev-log.md
└── README.md

.workspace/
├── config.yml
├── views.yml
├── fields.yml
├── publish.yml
├── agents.yml
└── issue-conventions.md
```

## GitHub Issue Convention

```markdown
## Summary

작업 요약

## Acceptance Criteria

- [ ] 완료 기준 1
- [ ] 완료 기준 2

## Plan

Due: 2026-06-24
Estimate: 4h
Sprint: week-1

## References

- docs/specs/api/auth-api.md
```

필수 labels:

- `status:todo`
- `status:doing`
- `status:blocked`
- `status:review`
- `status:done`
- `priority:p0`
- `priority:p1`
- `priority:p2`

## MVP 성공 데모

10분 안에 아래 흐름이 보여야 한다.

1. GitHub App 설치
2. code repo 선택
3. workspace repo 자동 생성
4. Home dashboard 확인
5. Home에서 회의록 생성
6. 두 명이 같은 회의록 동시 편집
7. 자동저장 상태 확인
8. 자동 publish 후 workspace repo commit 확인
9. GitHub Issues 가져오기
10. 보드/캘린더 확인
11. AI에게 기능 작업 분해 요청
12. issue 초안 승인 후 생성
13. AI에게 API 문서와 구현 차이 확인 요청
14. 문서 patch 또는 PR proposal 확인
15. macOS/Windows에서 설치형 앱처럼 실행

## 실패하지 않기 위한 규칙

- 2주 동안 P0 완성률을 높인다.
- code repo write를 열지 않는다.
- workspace repo는 서버 bot만 쓴다.
- GitHub Projects는 "꼭 필요하면 일부만" 붙인다.
- RAG는 embedding보다 source citation 품질을 먼저 본다.
- AI가 틀릴 수 있으므로 자동 실행 대신 approval UI를 둔다.
- 자동 publish는 conflict 발생 시 절대 overwrite하지 않는다.

## 최종 우선순위

1. Home dashboard가 팀 상황을 한눈에 보여주는 것
2. 작성 중 문서가 자동저장되고 복구되는 것
3. workspace repo에 깔끔하게 자동 publish되는 것
4. GitHub Issues를 잘 보여주고 등록/상태 변경하는 것
5. repo 내용을 근거로 AI가 답하는 것
6. AI가 issue와 문서 변경 초안을 만들어주는 것
7. 팀이 5주 동안 매일 쓸 수 있을 만큼 단순한 것
8. 브라우저 탭이 아니라 앱처럼 실행할 수 있는 것
