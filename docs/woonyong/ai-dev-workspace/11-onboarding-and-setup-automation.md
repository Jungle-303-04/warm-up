# Onboarding and Setup Automation

## Capability

사용자는 복잡한 GitHub 설정을 직접 하지 않아야 한다. `RepoPilot MVP`는 GitHub App 설치, code repo 선택, workspace repo 생성, labels/templates/webhook/indexing을 최대한 자동화하고, 사용자가 5분 안에 Home dashboard에 도착하게 해야 한다.

## User Flow

```text
1. GitHub로 시작하기
2. GitHub App 설치
3. code repo 선택
4. workspace repo 생성 또는 연결
5. 팀원 초대
6. 자동 세팅 실행
7. Home dashboard 진입
```

사용자에게 보이는 최소 입력:

```text
연결할 코드 레포
  team/project

협업 문서 저장소
  [x] 자동 생성: team/project-workspace
  [ ] 기존 repo 연결

프로젝트 시작일
  2026-06-20

프로젝트 기간
  5주

팀원
  GitHub usernames
```

## Setup Wizard

### Step 1. GitHub App 설치

사용자는 GitHub App 설치 화면에서 접근 가능한 repo를 선택한다.

설치 후 앱은 다음을 받는다.

- installation id
- account/org
- selected repositories
- granted permissions

앱은 권한이 부족하면 설정을 중단하지 말고, 어떤 기능이 제한되는지 보여준다.

```text
Issues write 권한 없음
-> 일감 보기 가능
-> 일감 생성/상태 변경 불가
```

### Step 2. Code Repo 선택

앱은 설치된 GitHub App이 접근 가능한 repo 목록만 보여준다.

선택 후 수행:

- default branch 확인
- language/package hints 확인
- README 확인
- source path 후보 탐색
- GitHub Issues 활성화 여부 확인
- labels 목록 확인
- PR 목록 확인

### Step 3. Workspace Repo 생성

옵션:

```text
자동 생성
  team/project-workspace

기존 repo 연결
  team/existing-workspace
```

자동 생성 시:

- private/public 기본값은 code repo와 동일하게 제안
- template files 생성
- `.workspace/` 설정 생성
- 첫 commit 생성

초기 commit:

```text
chore: initialize RepoPilot workspace
```

### Step 4. 기본 문서 생성

workspace repo에 다음을 만든다.

```text
docs/
├── README.md
├── project/
│   ├── goals.md
│   ├── roadmap.md
│   └── milestones.md
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
└── retrospectives/
    └── README.md

.workspace/
├── config.yml
├── views.yml
├── fields.yml
├── publish.yml
├── agents.yml
└── issue-conventions.md
```

### Step 5. GitHub Labels 생성

code repo에 필수 labels가 없으면 생성한다.

```text
status:todo
status:doing
status:blocked
status:review
status:done

priority:p0
priority:p1
priority:p2

type:feature
type:bug
type:docs
type:chore
type:research
```

이미 존재하면 색상/설명을 덮어쓰지 않고 유지한다.

### Step 6. Issue Convention 생성

issue body convention:

```md
## Summary

## Acceptance Criteria

- [ ] 

## Plan

Due: YYYY-MM-DD
Estimate: 0h
Sprint: week-1

## References

- 
```

앱은 이 convention을 기준으로 due date, estimate, sprint를 파싱한다.

### Step 7. Webhook 등록

GitHub App webhook으로 다음 이벤트를 받는다.

- issues
- issue_comment
- pull_request
- push
- label
- milestone

서버는 webhook payload를 즉시 처리하지 않고 queue에 넣는다.

```text
webhook received
-> signature verify
-> event log
-> sync job queue
-> local cache update
-> RAG stale mark
```

### Step 8. Initial Indexing

초기 색인 대상:

```text
workspace repo:
  docs/**
  .workspace/**

code repo:
  README.md
  package.json / pyproject.toml / build.gradle 등
  src/**
  app/**
  server/**
  tests/**
  docs/**
```

제외:

```text
.git/**
node_modules/**
dist/**
build/**
.env*
*.pem
*.key
*.crt
secrets/**
```

초기 색인 완료 후 Home에 표시:

```text
Repo connected
Issues synced: 24
Docs indexed: 8
Code files indexed: 132
AI ready
```

## Home First Experience

처음 진입한 홈은 빈 대시보드가 아니라 다음 행동을 유도해야 한다.

```text
오늘 해야 할 세팅
- 프로젝트 목표 작성
- kickoff 회의록 확인
- 팀원별 첫 일감 만들기
- API 문서 초안 만들기

AI 제안
- README를 보니 backend/frontend 구조가 있습니다.
- 초기 backlog를 만들까요?
- API 문서 템플릿을 생성할까요?
```

## Team Invite

팀원 초대는 GitHub username 또는 email로 한다.

앱 내부 role:

```text
Viewer
Writer
Publisher
Maintainer
Admin
```

초대받은 사용자가 GitHub repo 권한이 없으면:

- 앱 안에서 workspace 문서 보기/작성은 가능할 수 있음
- code repo 파일 조회는 제한됨
- issue write는 제한됨

정책은 workspace admin이 선택한다.

```text
Require GitHub repo access for all members: on/off
```

2주 MVP에서는 보안을 위해 `on`을 추천한다.

## Automatic Workspace Repo Naming

기본 규칙:

```text
<code-repo-name>-workspace
```

예시:

```text
team/project
-> team/project-workspace
```

이미 존재하면:

```text
project-workspace-2
또는 기존 repo 연결 선택
```

## Setup Failure Handling

| 실패 | 사용자 메시지 | 대응 |
|---|---|---|
| GitHub App 권한 부족 | 필요한 권한이 없습니다 | 재설치/권한 수정 링크 |
| workspace repo 생성 실패 | 저장소를 만들 수 없습니다 | 기존 repo 연결 옵션 |
| labels 생성 실패 | labels 일부 생성 실패 | 수동 복구 버튼 |
| initial indexing 실패 | AI 색인 실패 | retry, allowlist 수정 |
| webhook 등록 실패 | 실시간 GitHub sync 제한 | polling fallback |

## MVP Cutline

2주 MVP에서 반드시 자동화:

- GitHub App install callback 처리
- 접근 가능한 repo 목록 표시
- code repo 선택
- workspace repo 생성
- 기본 docs 생성
- 필수 labels 생성
- issues import
- initial indexing
- Home dashboard 진입

2주 MVP에서 미룰 수 있는 것:

- GitHub Projects v2 field 자동 생성
- organization-level member sync
- SSO/SCIM
- billing/team plan
- advanced repository ruleset 자동 설정
- CODEOWNERS 자동 설정

## Final Onboarding Goal

성공 기준:

```text
처음 온 사용자가 GitHub App 설치부터 Home dashboard 진입까지 5분 이내에 완료한다.
팀원은 첫날부터 Home에서 일정, 일감, 회의록, API 문서를 만들 수 있다.
```
