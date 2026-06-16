# 온보딩과 초기 설정 자동화

## 목표

사용자는 빠르게 첫 가치를 경험해야 한다. 첫 가치는 GitHub 로그인, repo 선택, 자동 분석, finding/proposal 확인이다.

## 설정 흐름

1. GitHub OAuth로 로그인한다.
2. 접근 가능한 repo 목록을 불러온다.
3. 분석할 repo를 선택한다.
4. 분석 branch 범위를 확인한다.
5. initial sync와 source indexing을 실행한다.
6. repo analysis dashboard를 보여준다.
7. finding과 proposal을 생성한다.
8. 사용자가 proposal을 승인하거나 보류한다.
9. 승인된 GitHub action을 실행하고 재-sync한다.

## 기본 페이지 트리

```text
Project
├── Start Here
├── Wiki
├── Meetings
├── Decisions
├── Specs
├── API Docs
├── Tasks
└── Archive
```

## 기본 뷰

- All items
- My tasks
- Kanban by status
- Calendar
- Stale docs
- Decisions
- Meetings

## Repository Role 선택

사용자는 repo를 다음처럼 라벨링할 수 있다.

- frontend
- backend
- infra
- docs
- package
- other

이 값은 검색, 필터링, AI 답변 품질을 높인다.

## 첫 indexing

Initial indexing은 다음을 수행한다.

- default branch, open PR branch, 최근 active branch 선택
- repo tree 읽기
- secret과 generated file 제외
- file/symbol metadata parsing
- issue와 PR 가져오기
- commit summary 가져오기
- basic retrieval chunk 생성
- 첫 code map 생성

## 팀 초대

Invite UX는 RepoLM 접근 권한과 GitHub 접근 권한이 다르다는 것을 설명해야 한다.

사용자에게 GitHub access가 없을 때:

- workspace role로 허용된 app page만 보여준다.
- private repo context를 숨긴다.
- repo-aware AI answer를 잠근다.
- access request/instruction 상태를 보여준다.

## 설정 실패 처리

자주 생기는 실패:

- repository 미선택
- GitHub token 만료 또는 revoke
- private repo 분석에 필요한 OAuth scope 부족
- 조직 SSO 미승인
- 사용자의 repo permission 부족
- GitHub API rate limit
- initial index 실패
- publish target 미설정

각 실패 상태는 다음을 보여준다.

- 무엇이 실패했는지
- 왜 중요한지
- 어떻게 재시도하는지
- 그래도 project를 사용할 수 있는지

권한 관련 실패는 `required_action`을 함께 보여준다.

```text
reconnect_github
grant_scope
authorize_sso
request_repo_access
wait_for_rate_limit
disconnect_repo
```

## MVP 첫 가치

첫 성공 세션은 다음 상태로 끝나야 한다.

- repo 연결 완료
- issue import 완료
- branch/docs/code/commit indexing 완료
- finding dashboard 확인
- 최소 하나의 GitHub issue/action proposal 확인
- 최소 하나의 stale/partial/missing finding 확인
