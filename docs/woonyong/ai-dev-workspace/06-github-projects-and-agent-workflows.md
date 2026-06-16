# GitHub 프로젝트와 에이전트 워크플로우

## GitHub 연동 범위

RepoLM은 GitHub를 대체하지 않고 연결한다.

MVP에서 읽는 것:

- repositories
- branches and commits
- issues
- PRs
- labels
- milestones
- assignees
- file contents

MVP에서 승인 후 쓰는 것:

- issue creation
- issue comments
- issue label/status metadata
- RepoLM item과 GitHub issue의 link

## Project와 Repository

Project가 제품 단위이고 Repository는 연결된 source다.

하나의 project는 다음을 연결할 수 있다.

- monorepo 하나
- frontend/backend 분리 repo
- infra repo
- docs repo
- experimental repo

각 repo는 indexing policy를 가질 수 있다.

## Issue Mapping

`WorkspaceItem(type=task)`는 필요할 때 GitHub issue와 매핑된다.

권장 매핑:

```text
task.title         -> issue title
task.body          -> issue body
task.assignee      -> issue assignee
task.status        -> label 또는 project field
task.due           -> due metadata/comment
task.related_code  -> Related Files section
task.doc_links     -> Related Docs section
```

## 에이전트 워크플로우 규칙

Agent는 proposal을 만든다. 조용히 project state를 바꾸지 않는다.

모든 proposal은 다음을 포함한다.

- action type
- target object
- evidence
- proposed change
- confidence
- risk notes
- approval state
- rollback 또는 correction path

## MVP 에이전트

### Repo Q&A Agent

문서, 이슈, PR, code chunk를 근거로 질문에 답한다. 반드시 source를 인용한다.

### Related Code Agent

문서와 관련된 code link를 추천한다. 승인 전까지 blue/suggested 상태다.

### Stale Link Agent

문서 검증 이후 연결된 file/symbol이 바뀌었는지 확인한다.

### Issue Planner Agent

계획 또는 meeting action item을 GitHub issue draft로 바꾼다.

### PR Summary Agent

PR을 읽고 task/document update를 제안한다.

### Meeting Action Agent

회의록에서 decision과 action item을 추출한다.

## 승인 UI

사용자는 다음을 볼 수 있어야 한다.

- 무엇이 바뀌는지
- agent가 왜 그렇게 판단했는지
- source citation
- confidence
- approve, edit, reject 버튼

## 안전 규칙

- 권한 없는 사용자에게 private repo context를 노출하지 않는다.
- 승인 없이 GitHub에 쓰지 않는다.
- MVP에서 merge나 code push를 하지 않는다.
- audit trail을 항상 남긴다.
- 근거가 약하면 불확실성을 표시한다.

## GitHub Issue Template

```md
## 목표

## 인수 기준

## 관련 문서

## 관련 코드

## 메모
```
