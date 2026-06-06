# GitHub Projects and Agent Workflows

## GitHub 연동 범위

MVP에서는 GitHub Issues와 Pull Requests를 중심으로 간다. GitHub Projects v2는 있으면 일부 status/date만 연결하고, 완전한 양방향 sync는 P1 이후로 둔다.

연동 대상은 두 repo로 나뉜다.

```text
code repo
  - Issues
  - PRs
  - code/read indexing
  - main 직접 push 금지

workspace repo
  - docs publish
  - action log
  - server bot write
```

필수:

- GitHub App 설치
- code repo 연결
- workspace repo 생성/연결
- issue 목록 조회
- issue 상세 조회
- issue 생성
- issue comment 추가
- issue assignee/label/milestone 수정
- PR 목록/상태 조회
- commit/file reference 조회
- workspace repo 자동 publish commit

P1:

- Project item status field 수정
- Project view sync
- issue dependency
- sub-issue
- PR review request
- code repo branch 생성
- code repo PR 생성
- release note 생성

## 내부 Task와 GitHub Issue 매핑

내부 task는 GitHub Issue와 1:1 또는 1:N으로 연결될 수 있다. 단, task의 최종 원본은 GitHub Issue다. GitHub Issue 생성 전에는 `task draft`로 Draft DB에 존재한다.

```yaml
task:
  id: task_auth_login
  title: Login API 구현
  status: In Progress
  github:
    repo: team/app
    issue_number: 42
    project_item_id: PVTI_xxx
    status_field_id: PVTSSF_xxx
```

동기화 방향:

- GitHub issue 변경 -> 내부 task 갱신
- 내부 board drag -> 승인 후 GitHub issue label/status 갱신
- AI action -> 내부 task와 GitHub issue 동시 갱신
- GitHub Project field sync는 P1 이후 또는 제한적으로만 적용

## Agent 1: 일감 마감 에이전트

사용자 요청:

```text
현재 일정과 현재 구현된 내용을 비교해서 반영된 내용의 일감을 마감해줘.
```

처리 순서:

1. 현재 sprint/milestone의 open issues 조회
2. 각 issue의 acceptance criteria 추출
3. 관련 문서, linked files, PR, commits 검색
4. 테스트/빌드 결과 확인 가능하면 반영
5. 완료 후보와 미완료 후보 분리
6. 완료 후보별 근거 요약
7. 승인 UI 표시
8. 승인된 항목만 issue comment 작성 및 status 변경

판단 근거:

- linked PR merged
- issue 제목/본문과 관련된 파일 변경
- 테스트 추가 또는 통과
- 문서 최신화
- acceptance criteria 충족
- blocker comment 없음

자동으로 하면 안 되는 것:

- 근거 없이 Done 처리
- 사용자 승인 없이 이슈 종료
- 실패한 테스트가 있는데 완료 처리
- 구현은 됐지만 문서가 명시적으로 요구된 일감을 완료 처리

## Agent 2: 일감 분해 에이전트

사용자 요청:

```text
지금 OAuth 로그인을 만들고 싶은데 무엇을 구현하고 일감을 어떻게 나눠야 하지?
```

출력:

- feature summary
- required docs
- task breakdown
- dependencies
- suggested owners
- suggested schedule
- GitHub issue drafts

작업 분해 예시:

```text
Epic: OAuth Login
├── API spec 작성
├── OAuth provider 설정
├── backend callback route 구현
├── session/token 저장 방식 결정
├── frontend login button 구현
├── e2e login test 작성
├── 보안 검토
└── 문서/README 업데이트
```

## Agent 3: API 문서 최신화 에이전트

사용자 요청:

```text
API 문서와 실제 구현된 API를 비교해서 다르면 실제 구현된 API 기준 문서를 최신화해줘.
```

처리:

1. API Markdown 문서 파싱
2. backend route/controller/schema 검색
3. OpenAPI 파일이 있으면 함께 비교
4. request/response/auth/error 차이 탐지
5. diff proposal 생성
6. 사용자 승인 후 workspace repo Markdown patch
7. code repo 반영이 필요하면 PR proposal 생성
8. dev history에 기록

비교 항목:

- method
- path
- auth requirement
- request body
- query params
- response status
- response schema
- error codes
- examples

## Agent 4: 회의록 액션 에이전트

회의록에서 다음을 추출한다.

- 결정사항
- 담당자
- 마감일
- action items
- blockers
- follow-up agenda

액션:

- task draft 생성
- GitHub Issue 생성
- ADR 문서 생성
- 다음 회의 일정 초안 생성
- workspace repo 자동 publish 대상 갱신

## Agent 5: 주간 리포트 에이전트

weekly-review 예제의 방식을 팀 프로젝트에 맞게 확장한다.

입력:

- GitHub Project 진행률
- issue status changes
- PR/commit activity
- docs updates
- meeting action items
- calendar events
- delayed tasks

출력:

- 주간 총평
- 완료된 일
- 지연된 일
- 위험한 일
- 문서 누락
- 다음 주 우선순위
- 팀원별 workload

## Agent 6: 문서 누락 탐지 에이전트

정기적으로 다음을 확인한다.

- 코드 변경은 있지만 관련 문서가 없는 경우
- 새 API route가 생겼지만 API 문서가 없는 경우
- issue는 Done인데 회고/개발 히스토리에 기록이 없는 경우
- 회의 결정사항이 task로 이어지지 않은 경우
- 오래된 문서가 최근 구현과 맞지 않는 경우

## Agent 7: RAG 답변 에이전트

일반 질문을 처리한다.

예시:

```text
현재 RAG 구현은 어디까지 됐어?
```

답변은 반드시 다음을 포함한다.

- 요약
- 관련 문서
- 관련 파일
- 관련 GitHub Issues/PRs
- 남은 작업
- 불확실한 점

## 승인 액션 UI

AI가 제안한 액션은 카드로 보여준다.

```text
Action: Close issue #42
Reason: PR #18 merged, src/auth/routes.ts and tests/auth.test.ts updated.
Change:
  GitHub Project Status: In Progress -> Done
  Issue Comment: "Implemented in PR #18..."
Buttons:
  Approve
  Edit comment
  Reject
```

code repo 관련 action은 더 강한 UI를 사용한다.

```text
Action: Create PR proposal
Target: code repo team/project
Reason: API docs need promotion to code repo README.
Change:
  Branch: repilot/docs-auth-api
  Files: docs/api/auth.md
Policy:
  main branch direct push is forbidden.
Buttons:
  Create PR
  Edit patch
  Reject
```

## 에이전트 안전 규칙

- 모든 write action은 승인 필요
- 파일 수정은 patch preview 필수
- GitHub 상태 변경은 comment와 함께 수행
- code repo main branch 직접 push 금지
- workspace repo publish는 publish worker만 수행
- workspace repo 자동 publish는 사용자 승인 없이 가능하지만 audit log 필수
- destructive action은 기본 비활성
- confidence가 낮으면 액션 대신 질문
- action log는 삭제하지 않음

## GitHub Project 필드 제안

| field | type | 설명 |
|---|---|---|
| Status | single select | Backlog/Ready/In Progress/Review/Done |
| Priority | single select | P0/P1/P2 |
| Assignee | user | 담당자 |
| Start | date | 시작일 |
| Due | date | 마감일 |
| Sprint | single select | Week 1~5 |
| Area | single select | FE/BE/AI/Infra/Docs |
| Evidence | text/number | AI 완료 근거 점수 |
| Docs | text | 관련 문서 링크 |

## GitHub Issue 템플릿

```md
## Goal

## Acceptance Criteria

- [ ]

## Related Docs

## Related Files

## Dependencies

## AI Notes
```
