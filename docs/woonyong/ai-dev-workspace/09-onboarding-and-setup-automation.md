# 온보딩과 초기 설정 자동화

## 목표

새 팀은 빠르게 첫 가치를 경험해야 한다. 첫 가치는 repo 연결, project data 확인, page/task 생성, read-only archive 퍼블리싱이다.

## 설정 흐름

1. 로그인한다.
2. Workspace를 만든다.
3. Project를 만든다.
4. GitHub App을 설치한다.
5. 하나 이상의 repo를 선택한다.
6. repo role을 확인한다.
7. initial sync와 code index를 실행한다.
8. default page tree를 생성한다.
9. 팀원을 초대한다.
10. 선택적으로 static viewer를 publish한다.

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

- repo tree 읽기
- secret과 generated file 제외
- file/symbol metadata parsing
- issue와 PR 가져오기
- basic retrieval chunk 생성
- 첫 code map 생성

## 팀 초대

Invite UX는 RepoPilot 접근 권한과 GitHub 접근 권한이 다르다는 것을 설명해야 한다.

사용자에게 GitHub access가 없을 때:

- workspace role로 허용된 app page만 보여준다.
- private repo context를 숨긴다.
- repo-aware AI answer를 잠근다.
- access request/instruction 상태를 보여준다.

## 설정 실패 처리

자주 생기는 실패:

- GitHub App 미설치
- repository 미선택
- 사용자의 repo permission 부족
- initial index 실패
- publish target 미설정

각 실패 상태는 다음을 보여준다.

- 무엇이 실패했는지
- 왜 중요한지
- 어떻게 재시도하는지
- 그래도 project를 사용할 수 있는지

## MVP 첫 가치

첫 성공 세션은 다음 상태로 끝나야 한다.

- repo 연결 완료
- issue import 완료
- project home 생성
- 최소 하나의 page 생성
- 최소 하나의 task view 확인
- 최소 하나의 code-doc link suggestion 확인
