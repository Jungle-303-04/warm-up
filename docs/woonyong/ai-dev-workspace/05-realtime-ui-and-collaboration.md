# 실시간 UI와 협업

## 제품 표면 분리

RepoLM은 두 가지 UI 모드를 가진다.

```text
Workspace App
로그인 기반, 협업 가능, 편집 가능

Static Viewer
공개/팀 읽기 전용, 필터 가능, 빠름
```

MVP의 협업 기능은 프로젝트 흐름을 증명하는 곳에만 투자한다.

## Workspace App

필수 화면:

- Project home
- Page tree
- Editor
- Table view
- Kanban view
- Calendar view
- Code relation panel
- AI proposals
- Publish settings

## Project Home

Home은 다음을 요약한다.

- 오늘의 회의와 일정
- 내 일감
- blocked 또는 stale work
- 최근 변경 문서
- stale 상태가 된 code-doc link
- 승인 대기 중인 AI proposal
- 주의가 필요한 GitHub issue

## Editor

Editor 요구사항:

- Markdown/MDX 친화적 작성
- title과 type selector
- 공통 속성 panel
- 관련 코드 chip
- publish state
- AI suggestion panel
- comment/note는 P1로 미룰 수 있음

## 실시간 협업

MVP 협업:

- 로그인 사용자는 같은 문서를 함께 편집할 수 있다.
- 사용자 presence가 보여야 한다.
- cursor/selection identity가 보여야 한다.
- 충돌은 realtime engine이 처리한다.
- static viewer는 realtime state에 참여하지 않는다.

추천 구현:

- editor model: Tiptap/ProseMirror
- realtime: Yjs + Hocuspocus, 또는 Liveblocks
- snapshot persistence: PostgreSQL

## Code Relation Panel

각 문서 페이지는 다음을 보여준다.

- 수동 연결 코드
- AI 추천 코드
- stale/broken 상태
- 마지막 검증 commit
- GitHub fallback link
- local VS Code link

예시:

```text
관련 코드
green  backend/app/auth/service.py issue_token()
yellow frontend/src/routes/login.tsx LoginForm
blue   backend/app/api/auth.py login_route() suggested
```

## 뷰

### Table

구조화된 검토와 필터링에 적합하다.

MVP column:

- title
- type
- status
- assignee
- due
- GitHub issue
- code status

### Kanban

`status` 기준으로 그룹화한다.

MVP status:

- todo
- in-progress
- blocked
- review
- done

### Calendar

`start`, `end`, `due`를 사용한다.

Calendar에 표시할 것:

- meeting
- due task
- schedule
- milestone

## Static Viewer

정적 viewer는 의도적으로 단순하게 만든다.

지원:

- page tree
- page reading
- 읽기 전용 table/kanban/calendar view
- filter와 search
- code-link chip
- stale/verified color state

지원하지 않음:

- editing
- comments
- AI action
- private repo data
- realtime presence

## VS Code 확장 후속

P1 extension 기능:

- 현재 file/symbol과 관련된 문서 표시
- 코드 옆 stale status 표시
- 선택한 코드로 related-code link 생성
- RepoLM page 열기

강한 차별점이지만, MVP에서는 브라우저 기반 code-link navigation이면 충분하다.
