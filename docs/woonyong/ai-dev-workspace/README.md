# AI Dev Workspace

현재 구현 기획명은 `RepoPilot MVP`다.

이 문서 묶음은 GitHub 저장소, Markdown 문서, 일정/일감/회의록/위키, 실시간 자동저장, RAG, AI 에이전트를 하나로 묶는 개발팀 협업툴 기획서다.

핵심 방향은 Notion 전체를 복제하는 것이 아니라, 2주 안에 5주 팀 프로젝트에서 바로 쓸 수 있는 GitHub 중심 협업 MVP를 만드는 것이다. 장기적으로는 고급 실시간 협업, Knowledge Map, MCP server까지 확장할 수 있지만, 첫 버전은 Home dashboard, GitHub Issues, workspace repo 문서, draft DB 자동저장, 자동 publish, 로컬 검색/RAG, 승인형 AI 액션에 집중한다.

## 제품 한 줄 정의

`RepoPilot MVP`는 code repo와 workspace repo를 연결해 팀의 코드, 이슈, 일정, 회의록, 위키, API 문서를 한 화면에서 운영하고, draft DB 자동저장과 AI/RAG로 5주 팀 프로젝트를 보조하는 2주 개발 가능 협업툴이다.

## 문서 목록

- [01. Reference Research](./01-reference-research.md)
- [02. Product Requirements](./02-product-requirements.md)
- [03. Information Architecture](./03-information-architecture.md)
- [04. Git, RAG, MCP Architecture](./04-git-rag-mcp-architecture.md)
- [05. Realtime UI and Collaboration](./05-realtime-ui-and-collaboration.md)
- [06. GitHub Projects and Agent Workflows](./06-github-projects-agents.md)
- [07. Roadmap and Development Items](./07-roadmap-and-development-items.md)
- [08. Two Week MVP Cutline](./08-two-week-mvp-cutline.md)
- [09. Home and Content UX Model](./09-home-and-content-ux-model.md)
- [10. Storage, Publish, Permissions, and Security](./10-storage-publish-permissions-security.md)
- [11. Onboarding and Setup Automation](./11-onboarding-and-setup-automation.md)
- [12. Web, PWA, and Desktop Distribution](./12-web-pwa-desktop-distribution.md)
- [13. AI Agent, RAG, MCP, and LangChain Plan](./13-ai-agent-rag-mcp-langchain-plan.md)

## 핵심 설계 원칙

1. code repo와 workspace repo는 분리한다.
2. code repo는 코드 형상관리 원본이며, 앱은 기본적으로 읽고 분석한다.
3. workspace repo는 회의록, 위키, API 문서, 개발 히스토리, AI action log의 Git 원본이다.
4. Draft DB는 실시간 편집과 자동저장의 원본이다.
5. Git commit은 사용자의 매 입력이 아니라 자동 publish job이 안정적인 시점에 만든다.
6. 일정, 일감, 회의록, 위키, 개발 히스토리는 하나의 `Workspace Item` 모델 위에서 여러 뷰로 보여준다.
7. AI는 채팅만 하지 않고, GitHub Issue, 문서, 코드, 일정에 대해 근거 기반 action proposal을 만든다.
8. code repo 변경은 직접 push가 아니라 PR proposal로만 보낸다.
9. 권한은 사용자 OAuth와 GitHub App installation 권한을 분리한다.
10. 에이전트 액션은 근거, 변경 전후, 되돌리기 경로, audit log를 항상 남긴다.

## 제품 범위 요약

```text
RepoPilot MVP
├── Home Dashboard
│   ├── today schedule
│   ├── my work
│   ├── blocked/overdue
│   ├── recent docs/meetings/decisions
│   ├── AI alerts
│   └── approvals
├── Code Repo Integration
│   ├── code read/index
│   ├── issues
│   ├── pull requests
│   ├── labels/milestones
│   └── PR-only promotion
├── Workspace Repo
│   ├── meetings
│   ├── wiki
│   ├── API/spec docs
│   ├── decisions
│   ├── dev history
│   └── action logs
├── Draft Collaboration Layer
│   ├── autosave
│   ├── snapshots
│   ├── type properties
│   ├── auto publish queue
│   └── conflict handling
├── Views
│   ├── board
│   ├── calendar
│   ├── docs
│   ├── meetings
│   └── wiki
├── AI
│   ├── repo-aware chat
│   ├── RAG retrieval
│   ├── issue split proposal
│   ├── close issue proposal
│   ├── API doc drift proposal
│   ├── meeting action extraction
│   ├── internal tool registry
│   └── optional MCP/LangGraph expansion
└── Security
    ├── GitHub App
    ├── app roles
    ├── token isolation
    ├── secret filtering
    └── audit log
└── Distribution
    ├── web app
    ├── installable PWA
    ├── optional Tauri desktop shell
    └── macOS/Windows packages
```

## MVP 판단 기준

2주 MVP는 기능 수가 아니라 다음 데모가 가능한지로 판단한다.

1. GitHub App 설치 후 code repo를 선택하면 앱이 repo, issues, PR, labels를 읽어 Home dashboard를 구성한다.
2. 앱이 workspace repo를 자동 생성하거나 기존 workspace repo를 연결한다.
3. Home에서 일정, 일감, 회의록, 문서, 위키, API 문서를 생성하고 타입을 바꿀 수 있다.
4. 작성 중인 문서는 Draft DB에 자동저장되고, 안정적인 시점에 workspace repo로 자동 publish된다.
5. GitHub Issues를 보드, 캘린더, 담당자 필터로 볼 수 있고, 홈에서 바로 등록할 수 있다.
6. AI에게 "이 기능을 만들려면 일감을 어떻게 나눌까?"라고 물으면 기존 문서/코드/이슈를 근거로 GitHub Issue 초안을 만든다.
7. AI에게 "현재 구현과 일정이 맞는지 확인하고 완료된 일감을 마감해줘"라고 요청하면 근거를 제시하고 승인 후 issue comment/status를 바꾼다.
8. API 문서와 실제 구현이 다르면 AI가 차이를 요약하고, workspace repo 문서 patch 또는 code repo PR 초안을 만든다.
9. 웹앱은 PWA로 설치 가능해야 하며, macOS/Windows 앱 패키지는 같은 frontend를 Tauri shell로 감싸는 확장 경로를 둔다.

명시적으로 2주 MVP에서 제외하는 항목:

- 팀원 마우스 포인터와 화면 동기화
- 완전한 GitHub Projects v2 양방향 동기화
- 여러 레포의 완전한 dependency graph
- code repo 직접 자동 커밋/자동 머지
- 사용자의 GitHub 권한을 우회하는 write action
