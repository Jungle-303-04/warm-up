# 정보 구조

## 핵심 결정

RepoPilot은 문서, 일감, 회의록, 일정, 결정, spec을 하나의 콘텐츠 모델로 다룬다. UI는 item type과 property에 따라 적절한 뷰를 선택한다.

이 방식은 wiki, task, calendar, issue 시스템을 각각 따로 만드는 것보다 단순하다.

MVP의 사용자-facing 시작점은 `Project` 생성이 아니라 GitHub repo 연결이다. `RepositoryConnection`이 분석과 자동화의 기준 단위이며, `Workspace`와 `Project`는 나중에 여러 repo를 묶는 내부 그룹핑 개념으로 확장한다.

## 주요 객체

```text
Workspace
Project
RepositoryConnection
BranchSnapshot
SourceFile
SourceChunk
WorkspaceItem
View
GitHubIssueLink
CodeReference
DocCodeLink
PublishSnapshot
Finding
AgentProposal
AuditEvent
```

## RepositoryConnection

`RepositoryConnection`은 사용자가 OAuth로 연결한 GitHub repo를 나타낸다.

필수 필드:

- `id`
- `user_id`
- `provider`
- `owner`
- `repo`
- `url`
- `default_branch`
- `visibility`
- `permission`
- `status`: `active | disconnected | cleanup_pending | deleted`
- `last_synced_at`

repo 연결 해제는 GitHub 원본 repo를 삭제하지 않는다. RepoPilot 내부 source, chunk, embedding, finding, proposal을 inactive 처리하고 검색에서 제외한다.

## Source File과 Chunk

`SourceFile`은 repo에서 수집한 코드, Markdown 문서, issue, PR, commit 같은 원본 단위다.

```text
repository_connection_id
branch
commit_sha
source_type: code | doc | issue | pr | commit
path_or_external_id
content_hash
is_active
deleted_at
```

`SourceChunk`는 검색과 RAG를 위한 파생 단위다.

```text
source_file_id
chunk_type: document_heading | code_file | code_symbol | issue_body | pr_body | commit_summary
text
chunk_hash
embedding_id
is_active
deleted_at
```

Vector DB는 `SourceChunk` 검색용이며, 상태 판단의 source of truth는 App DB다.

## Workspace Item

`WorkspaceItem`은 모든 사용자-facing page와 work item의 공통 레코드다.

필수 필드:

- `id`
- `workspace_id`
- `project_id`
- `type`
- `title`
- `slug`
- `parent_id`
- `body`
- `properties`
- `visibility`
- `publish_state`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

MVP item type:

- `wiki`
- `task`
- `meeting`
- `decision`
- `spec`
- `api_doc`
- `schedule`
- `milestone`

## 공통 속성

공통 속성은 뷰와 필터의 기준이 된다.

```yaml
status: todo | in-progress | blocked | done | archived
assignee: user_id
start: date
end: date
due: date
tags: string[]
repo_refs: repo_id[]
github_issue: owner/repo#number
related_code: CodeReference[]
visibility: private | team | public
publish_state: draft | published | stale | hidden
```

타입별 속성은 `properties` 안에 둔다. 다만 첫 버전에서는 완전한 schema builder를 만들지 않는다.

## Markdown/MDX 아카이브 포맷

퍼블리싱 또는 export된 item은 frontmatter와 Markdown/MDX body로 표현한다.

```md
---
id: item_123
type: decision
status: accepted
tags: [auth, security]
related_code:
  - repo: backend
    path: app/auth/service.py
    symbol: issue_token
    commit: abc123
    status: verified
---

# JWT Token Policy

...
```

## 뷰

View는 `WorkspaceItem`에 대한 저장된 필터다.

```text
Table    -> 전체 item list
Kanban   -> status 기준 그룹
Calendar -> start/end/due가 있는 item
Timeline -> milestone과 schedule
Docs     -> parent/slug 기준 트리
```

정적 viewer에서는 읽기 전용 필터와 정렬만 제공하면 충분하다.

## 페이지 트리

페이지 트리는 `WorkspaceItem.parent_id` 기반 계층 구조다.

기본 섹션 예시:

```text
Project
├── Wiki
├── Meetings
├── Decisions
├── Specs
├── API Docs
├── Tasks
└── Archive
```

Task는 tree에도 나타나고 task view에도 동시에 나타날 수 있다.

## Code Reference

`CodeReference`는 코드 위치를 식별한다.

```text
repo_id
file_path
symbol_name
start_line
end_line
commit_sha
github_url
local_uri
```

`DocCodeLink`는 문서와 코드의 관계 상태를 저장한다.

```text
item_id
code_reference_id
source: manual | ai | github | import
confidence
status: verified | stale | broken | suggested
last_verified_commit
last_checked_at
```

## 상태 색상 의미

- Green: `verified`
- Yellow: `stale`
- Red: `broken`
- Blue: `suggested`
- Gray: no relation

## 퍼블리싱 규칙

Publishing은 정적 snapshot을 만든다.

퍼블리싱 가능:

- public/team wiki page
- publishable로 표시된 spec과 decision
- 읽기 전용 task/calendar/kanban view
- 공개해도 안전한 code link

퍼블리싱 불가:

- private page
- secret
- pending AI proposal
- unpublished draft
- viewer 권한이 없는 repo content

## 로컬 열기와 GitHub fallback

code link 처리 순서:

1. 사용자의 local repo path가 설정되어 있으면 VS Code URI를 생성한다.
2. 없으면 GitHub URL을 생성한다.
3. commit SHA가 있으면 permalink를 사용한다.
4. 없으면 current branch URL을 사용하고 moving link로 표시한다.

## 데이터 소유권

- App DB: 실시간 편집 상태, view, permission, proposal, link status
- GitHub: code, issue, PR, label, repo permission
- Markdown/MDX export: 장기 보관과 정적 퍼블리싱
- Vector DB: search/retrieval index이며 재생성 가능
