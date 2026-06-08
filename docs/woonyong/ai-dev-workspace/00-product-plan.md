# 제품 기획서

## 제품 정의

`RepoPilot`은 개발팀이 문서, 일감, 일정, GitHub 이슈, 실제 코드의 관계를 한 프로젝트 안에서 관리하도록 돕는 협업 워크스페이스다.

사용감은 Notion처럼 페이지와 뷰를 만들 수 있고, Obsidian/Quartz처럼 Markdown 기반 아카이브와 정적 퍼블리싱이 가능하며, GitHub Projects/Linear처럼 개발 일감을 다룰 수 있어야 한다. 하지만 핵심은 또 다른 Notion을 만드는 것이 아니다. 핵심 차별점은 **프로젝트 지식이 현재 코드와 얼마나 맞는지 보여주는 것**이다.

## 한 줄 포지셔닝

RepoPilot은 Markdown 문서, 일감 뷰, GitHub 이슈, 코드 참조를 연결하고 이를 정적 프로젝트 아카이브로 퍼블리싱할 수 있는 코드 인지형 프로젝트 지식베이스다.

## 목표 사용자

- GitHub를 쓰지만 문서와 이슈가 자주 따로 노는 작은 개발팀
- 공개 문서와 기여자 친화적인 작업 흐름이 필요한 오픈소스 운영자
- 큰 프로젝트 관리 도구 없이 문서, 일감, repo-aware AI를 쓰고 싶은 초기 스타트업 팀
- 프로젝트 과정 기록과 회고가 중요한 부트캠프, 연구팀, 스터디 팀
- 에이전트 기반 개발을 많이 하며 작업, 결정, 프롬프트, 코드 변경의 근거를 남겨야 하는 팀

## 해결하려는 문제

팀은 계획을 Notion이나 Markdown에 쓰고, 구현은 GitHub에서 하고, 일감은 이슈로 관리한다. 시간이 지나면 문서는 낡고, 이슈에는 구현 근거가 부족해지며, 새 팀원은 코드가 왜 이렇게 작성되었는지 찾기 어렵다.

RepoPilot은 반복되는 세 가지 비용을 줄여야 한다.

1. 코드 변경 뒤에 있는 문서나 의사결정을 찾는 비용
2. 문서가 현재 구현과 맞는지 확인하는 비용
3. 회의, 계획, 구현 변경을 최신 이슈와 프로젝트 히스토리로 반영하는 비용

## 제품 원칙

1. 프로젝트가 최상위 단위다. 하나의 프로젝트는 여러 GitHub repo를 연결할 수 있다.
2. 중요한 정보는 모두 페이지 또는 레코드이며, 공통 속성을 가진다.
3. 작성/협업 영역은 동적이어도, 공개/공유 뷰어는 정적이고 빠르고 단순해야 한다.
4. Markdown/MDX는 장기 보관과 퍼블리싱을 위한 내구성 있는 포맷이다.
5. `status`, `assignee`, `due`, `tags` 같은 구조화 속성이 table, kanban, calendar, timeline 뷰를 만든다.
6. GitHub는 코드, 이슈, PR, repo 권한의 원본이다.
7. AI는 근거를 가진 제안을 만들고, 사용자가 승인한 뒤에만 write action을 실행한다.
8. 코드-문서 연결은 단순 URL이 아니라 제품의 핵심 객체다.
9. MVP는 Notion 기능 복제가 아니라 코드-문서 정합성 검증에 집중한다.

## 핵심 모델

```text
Workspace
└── Project
    ├── Pages
    │   ├── Wiki
    │   ├── Meeting
    │   ├── Decision
    │   ├── Spec
    │   └── API Doc
    ├── Work Items
    │   ├── Task
    │   ├── Milestone
    │   └── Schedule
    ├── Views
    │   ├── Table
    │   ├── Kanban
    │   ├── Calendar
    │   └── Timeline
    ├── Repositories
    │   ├── frontend
    │   ├── backend
    │   └── infra
    └── Published Site
```

## 통합 아이템 타입

문서, 일감, 회의록, 일정이 각자 별도 시스템이 되면 MVP가 커진다. 하나의 `WorkspaceItem` 모델을 두고 `type`과 공통 속성으로 구분한다.

공통 속성:

- `type`: `wiki`, `task`, `meeting`, `decision`, `spec`, `api_doc`, `schedule`, `milestone`
- `title`
- `status`
- `assignee`
- `due`
- `start`
- `end`
- `tags`
- `project`
- `repo_refs`
- `github_issue`
- `related_code`
- `visibility`
- `publish_state`

예시 frontmatter:

```yaml
---
type: task
status: in-progress
assignee: woonyong
due: 2026-06-20
github_issue: owner/repo#42
related_code:
  - repo: backend
    path: app/api/auth.py
    symbol: login
    status: stale
---
```

## 작성 영역과 정적 뷰어

제품은 두 표면으로 나눈다.

```text
Workspace App
실시간 편집, 권한, AI, GitHub sync, repo indexing

        publish/build

Static Viewer
읽기 전용 페이지, 필터, 검색, 공개 아카이브
```

정적 뷰어는 전체 앱을 복제하지 않는다. 정적 뷰어가 제공할 것은 다음 정도면 충분하다.

- 페이지 트리
- 문서 페이지
- 읽기 전용 table/kanban/calendar
- 필터
- 검색
- 공개 가능한 코드 링크
- stale/verified 코드-문서 상태 표시

## 코드-문서 연결

코드-문서 관계가 제품의 핵심 차별점이다.

문서에는 관련 코드가 칩 형태로 표시된다.

```text
관련 코드
[auth_service.py:login] [routes/auth.ts] [User model]
```

클릭 동작:

1. 로컬 repo 경로가 설정되어 있으면 `vscode://file/...`로 VS Code를 연다.
2. 로컬 경로가 없으면 GitHub 파일 또는 심볼 링크로 이동한다.
3. 검증된 commit이 있으면 히스토리 정확성을 위해 GitHub permalink를 우선한다.
4. 심볼이 이동했으면 최신 감지 위치를 보여주고 changed/stale 상태로 표시한다.

상태 색상:

- 초록: 현재 코드 참조 기준 검증됨
- 노랑: 문서 검증 이후 연결된 코드가 변경됨
- 빨강: 연결된 파일 또는 심볼이 사라짐
- 파랑: AI가 추천했지만 아직 사람이 승인하지 않음
- 회색: 연결 없음

## VS Code 확장 방향

VS Code 확장은 첫 제품 조각의 필수 기능은 아니지만 강한 후속 차별점이다.

최소 확장 기능:

- 현재 파일 또는 심볼과 관련된 문서/일감 표시
- 코드 옆에 stale/verified 상태 표시
- 연결된 RepoPilot 문서 열기
- 현재 선택 영역으로 코드-문서 링크 생성 또는 추천

이 기능은 코드에 붙는 프로젝트 지식용 CodeLens처럼 느껴져야 한다.

## GitHub 연동

GitHub 연동은 좁게 시작한다.

MVP:

- 하나의 GitHub 계정/조직과 하나 이상의 repo 연결
- 이슈, PR, label, milestone, assignee 가져오기
- `WorkspaceItem`과 GitHub issue 연결
- task 또는 meeting action item에서 issue draft 생성
- 사용자가 승인한 뒤에만 issue status/comment 변경
- repo 내용을 검색/RAG용으로 인덱싱

MVP에서 하지 않는 것:

- GitHub Projects v2 전체 대체
- 자동 merge 또는 code repo 직접 push
- GitHub 권한 우회
- 모든 repo의 완전한 dependency graph

## AI의 역할

AI는 자율 프로젝트 매니저가 아니라 근거 기반 보조자다.

MVP AI action:

- "이 문서와 관련된 코드는 어디야?"에 답하기
- 문서에 관련 코드 링크 추천
- 코드 변경 후 stale 문서-코드 링크 감지
- 계획을 GitHub issue draft로 분해
- PR을 요약하고 task/document 업데이트 제안
- 회의록에서 action item 추출

모든 write action은 다음을 포함해야 한다.

- 근거
- 제안 diff 또는 목표 상태
- confidence
- 승인 상태
- audit log

## MVP 범위

가장 작은 버전에서 다음을 증명한다.

1. 프로젝트에 하나 이상의 GitHub repo를 연결한다.
2. Markdown/MDX 페이지 트리를 만든다.
3. 공통 속성과 typed page를 제공한다.
4. task를 table, kanban, calendar로 볼 수 있다.
5. GitHub issue 연결과 issue draft 생성을 제공한다.
6. 파일/심볼 단위 코드 인덱싱을 한다.
7. 문서에 관련 코드 칩을 표시한다.
8. 코드-문서 링크의 stale/verified 상태를 표시한다.
9. 필터와 검색이 가능한 정적 viewer를 퍼블리싱한다.
10. 로그인 사용자에게 기본 실시간 presence가 있는 편집 경험을 제공한다.

## 명시적 제외 범위

- 완전한 Notion 클론
- 완전한 Linear 클론
- 코드-문서 정합성을 증명하기 전의 Google Docs급 에디터
- MVP 단계의 필수 데스크톱 앱
- 승인 없는 AI의 GitHub write
- 기본 읽기에 앱 서버가 필요한 public viewer

## 성공 기준

MVP가 유용하다고 판단하는 기준:

1. repo를 연결할 수 있다.
2. wiki/task/meeting page를 만들 수 있다.
3. task를 kanban과 calendar로 볼 수 있다.
4. 문서와 코드를 연결할 수 있다.
5. 코드 변경 후 낡은 문서가 표시된다.
6. 코드 링크를 클릭하면 VS Code 또는 GitHub로 이동한다.
7. 읽기 전용 프로젝트 아카이브를 퍼블리싱할 수 있다.

## 추천 스택

- Frontend: React 또는 Next.js
- Editor: Tiptap/ProseMirror
- Realtime: Yjs + Hocuspocus, 또는 managed infra를 원하면 Liveblocks
- Backend: FastAPI
- Database: PostgreSQL + pgvector
- Queue/cache: Redis
- Repo parsing: tree-sitter + 언어별 fallback parser
- GitHub integration: GitHub App
- Static publishing: Markdown/MDX to HTML build pipeline
- AI: 승인 기반 tool을 가진 retrieval-first agent

## 제품 가설

개발팀은 더 예쁜 위키만 필요한 것이 아니다. 문서, 일감, 이슈, 코드 경로가 서로 어떻게 연결되어 있는지 알고, 그 연결이 낡았을 때 경고해주는 프로젝트 메모리가 필요하다.
