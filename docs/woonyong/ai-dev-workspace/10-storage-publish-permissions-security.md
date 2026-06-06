# Storage, Publish, Permissions, and Security

## Capability

사용자는 Notion처럼 자동 저장되는 경험을 가져야 한다. 하지만 내부적으로는 모든 편집을 Git commit으로 만들면 안 된다. `RepoPilot MVP`는 Draft DB에 계속 자동저장하고, 안정적인 시점에 workspace repo로 자동 publish하며, code repo 변경은 PR proposal로만 보낸다.

## Storage Contract

```text
Auto Save
  - 매 입력/변경을 Draft DB에 저장
  - 유저 화면에는 "저장됨"으로 표시
  - Git commit 아님

Auto Snapshot
  - 복구 가능한 버전을 DB에 주기적으로 저장
  - 브라우저 종료/네트워크 끊김 후 복원 가능
  - Git commit 아님

Auto Publish
  - 조건이 맞으면 workspace repo에 Markdown snapshot commit
  - 서버 bot만 수행
  - 유저가 버튼을 누르지 않아도 됨

Promote
  - code repo에 반영이 필요하면 PR proposal 생성
  - main branch 직접 push 금지
```

## User Visible Save States

사용자는 내부 저장소를 몰라도 된다. 화면에는 다음 상태만 보여준다.

| 표시 | 내부 의미 |
|---|---|
| `저장 중...` | Draft DB write 진행 |
| `저장됨` | Draft DB autosave 완료 |
| `Git 기록 대기 중` | publish rule 대기 또는 queue 대기 |
| `Git에 기록됨 11:03` | workspace repo commit 완료 |
| `충돌 발생` | publish conflict |
| `GitHub 권한 필요` | GitHub App 권한 부족 |

## Publish Rule Engine

자동 publish는 rule engine이 판단한다.

입력:

- item type
- last edit time
- active editor count
- content hash
- meeting start/end time
- last published hash
- max unpublished duration
- conflict state

출력:

- `skip`
- `queue_publish`
- `require_attention`

예시:

```ts
type PublishDecision =
  | { kind: "skip"; reason: string }
  | { kind: "queue_publish"; itemId: string; reason: string }
  | { kind: "require_attention"; reason: string }
```

## Publish Rules

| 타입 | 자동 publish 조건 |
|---|---|
| meeting | `endAt` 이후, 마지막 편집 5분 경과, active editor 없음 |
| document | 마지막 편집 10분 경과 |
| wiki | 마지막 편집 10분 경과 |
| api_doc | 마지막 편집 10분 경과 또는 AI patch 승인 |
| decision | status가 `review` 또는 `final`로 바뀜 |
| dev_log | 하루 1회 또는 30분 batch |
| action_log | 10분 batch |

공통 조건:

- 빈 문서 publish 금지
- 같은 content hash publish 금지
- 한 item당 최소 publish 간격 5분
- 최대 미게시 시간 30분
- workspace repo lock 필요
- conflict 상태면 publish 금지

## Publish Worker

publish worker는 workspace repo write를 직렬화한다.

```text
1. publish_jobs에서 대기 job 선택
2. workspace repo lock 획득
3. GitHub App installation token 발급
4. workspace repo pull
5. Draft DB 내용을 Markdown + frontmatter로 materialize
6. target path 계산
7. 파일 write
8. git diff 확인
9. 변경 없음이면 skip
10. commit
11. push
12. lastPublishedAt, lastPublishedHash 갱신
13. audit log 기록
14. lock 해제
```

## Type Property Materialization

publish worker는 Draft DB의 모든 속성을 그대로 frontmatter에 쓰지 않는다. 타입 변경으로 보관된 이전 속성까지 모두 publish하면 Markdown 문서가 지저분해지고, RAG metadata도 흐려진다.

materialize 원칙:

```text
Draft DB
  coreProperties
  typeProperties[currentType]
  archivedTypeProperties
  extraProperties

Published Markdown
  coreProperties
  typeProperties[currentType]
  compatible shared properties
  relation metadata
  typeHistory summary
```

publish에서 제외되는 값:

- 이전 타입 전용 속성
- 현재 schema에 없는 extra properties
- UI 임시 상태
- cursor/presence
- autosave 내부 상태

제외된 값은 삭제하지 않고 Draft DB, item_versions, audit_logs에 보존한다.

정책:

- publish worker는 타입 불일치 속성을 자동 삭제하지 않는다.
- 이전 타입 속성 삭제는 사용자 명시 action으로만 가능하다.
- 삭제 action은 audit log를 남긴다.
- 타입 변경 후 path가 바뀌면 이전 파일은 redirect/superseded 문서로 남긴다.

Commit message format:

```text
docs(<type>): autosync <title>
```

예시:

```text
docs(meeting): autosync 2026-06-20 kickoff
docs(api): autosync auth api spec
docs(wiki): autosync glossary
chore(action-log): record ai actions 2026-06-20
```

## Conflict Policy

자동 publish는 절대 외부 변경을 덮어쓰지 않는다.

충돌 가능 상황:

- 누군가 workspace repo에 직접 push
- 같은 파일에 다른 publish job이 동시 접근
- path 변경 중 이전 파일과 새 파일이 충돌
- GitHub push 실패 또는 branch protection 영향

처리:

```text
1. publish 중단
2. item status = conflict
3. conflict snapshot 저장
4. Home Approvals에 노출
5. 사용자가 resolve
6. 재publish
```

충돌 해결 옵션:

- Draft DB 버전 사용
- workspace repo 버전 사용
- 수동 merge
- 새 파일/path로 publish

## Repository Separation

### code repo

용도:

- 실제 코드
- 테스트
- 배포
- PR
- GitHub Issues

정책:

- 앱은 기본적으로 contents read
- issues read/write 가능
- PR read/write 가능
- main branch 직접 push 금지
- 문서 반영이 필요하면 PR proposal 생성

### workspace repo

용도:

- 회의록
- 위키
- API 문서
- 의사결정
- 개발 히스토리
- AI action log

정책:

- 서버 bot만 contents write
- 팀원은 앱 UI를 통해 작성
- GitHub에서 직접 수정은 권장하지 않음
- 자동 publish commit 허용

## Permission Model

권한은 두 겹이다.

```text
GitHub permission
  - GitHub App이 repo에 접근할 수 있는지

App role
  - 이 사용자가 앱 안에서 어떤 행동을 할 수 있는지
```

### App roles

| Role | 권한 |
|---|---|
| Viewer | Home, docs, issues 보기 |
| Writer | draft 작성, schedule 생성, meeting 작성 |
| Publisher | conflict 해결, final 표시, workspace publish 정책 관리 |
| Maintainer | issue 생성/수정/comment/status 변경 승인 |
| Admin | repo 연결, GitHub App 설정, 멤버/권한 관리 |

### Required GitHub App permissions

| Repo | Permission | Access | 이유 |
|---|---|---|---|
| code repo | Metadata | read | repo 정보 |
| code repo | Contents | read | 코드/RAG indexing |
| code repo | Issues | read/write | 일감 관리 |
| code repo | Pull requests | read/write | PR proposal |
| workspace repo | Metadata | read | repo 정보 |
| workspace repo | Contents | read/write | 자동 publish |

선택 권한:

- Projects: GitHub Projects v2 field sync를 붙일 때
- Commit statuses/checks: Done Evidence Score 고도화 시
- Workflows: MVP에서는 요청하지 않는다.

## Auth Flow

```text
User login with GitHub OAuth
-> app user 생성
-> GitHub App installation 확인
-> workspace membership 확인
-> app role 확인
-> server generates installation token when needed
-> GitHub API call
```

원칙:

- 사용자 브라우저에 GitHub installation token을 내려주지 않는다.
- GitHub App private key는 서버 secret으로만 저장한다.
- installation token은 필요할 때 서버에서 발급하고 만료되면 재발급한다.
- user OAuth token과 installation token을 혼동하지 않는다.

## Security Risks and Controls

| 위험 | 대응 |
|---|---|
| AI가 code repo를 망침 | code repo 직접 push 금지, PR proposal만 |
| 문서 커밋이 코드 히스토리 오염 | workspace repo 분리 |
| 자동 publish 폭주 | debounce, 최소 publish 간격, content hash check |
| workspace repo 충돌 | repo lock, conflict state, 자동 overwrite 금지 |
| token 유출 | 서버 secret 저장, client token 노출 금지 |
| private code 유출 | path allowlist, secret filter, 답변 redaction |
| webhook 위조 | signature 검증 |
| 권한 없는 issue 변경 | app role + GitHub App permission 검사 |
| AI prompt injection | repo 문서는 명령이 아니라 참고자료로 처리 |
| 누가 바꿨는지 모름 | audit log, action log, commit bot attribution |

## Audit Log

모든 중요한 변경은 `audit_logs`에 남긴다.

기록 대상:

- draft 생성/삭제
- type 변경
- auto publish success/failure
- GitHub issue 생성/수정/comment
- AI proposal 생성
- AI proposal 승인/거절
- PR proposal 생성
- 권한 변경
- repo 연결/해제

예시:

```json
{
  "actorType": "user",
  "actorId": "user_123",
  "action": "approve_issue_creation",
  "targetType": "github_issue",
  "targetId": "#42",
  "workspaceId": "ws_123",
  "evidence": ["docs/specs/api/auth-api.md", "src/routes/auth.ts"],
  "createdAt": "2026-06-20T11:03:00+09:00"
}
```

## MVP Implementation Notes

2주 MVP에서 가장 현실적인 선택:

- Draft DB는 SQLite 또는 Postgres 중 하나를 선택하되, 배포/협업 서버를 고려하면 Postgres가 더 안전하다.
- 로컬 개발/데모만 보면 SQLite도 가능하다.
- 실시간 편집은 Yjs + WebSocket을 쓰되, presence는 최소화한다.
- workspace repo publish worker는 queue 기반으로 단일 worker부터 시작한다.
- code repo write는 MVP에서 PR proposal만 만들고 main push는 구현하지 않는다.
