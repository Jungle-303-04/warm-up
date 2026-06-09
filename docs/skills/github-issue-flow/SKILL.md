---
name: github-issue-flow
description: Use when turning Notion tasks, meeting action items, specs, or project plans into GitHub issue drafts, branch names, PR descriptions, and status updates while preserving evidence and requiring approval before GitHub writes.
---

# GitHub Issue Flow

## 기준

GitHub는 구현 흐름의 실행 기록이다.
Notion은 회의, 프로젝트, 작업의 운영 기준이다.
둘은 연결하되, 아무 근거 없이 자동으로 쓰지 않는다.

승인 없는 GitHub write action은 하지 않는다.
먼저 issue draft와 근거를 만든다.

## 입력 기준

다음 입력을 GitHub issue draft로 바꿀 수 있다.

- Notion `작업`
- 회의 후속 조치
- 제품 요구사항
- 스펙 문서
- 버그 리포트
- PR 이후 필요한 문서/작업 업데이트

## Issue Draft 형식

```md
## 목표

## 인수 기준

## 관련 문서

## 관련 코드

## 메모
```

제목은 작업자가 바로 이해할 수 있게 쓴다.
너무 큰 작업이면 여러 issue로 나눈다.

## 매핑 규칙

- Notion 작업 이름 -> issue title
- 작업 본문 또는 회의 후속 조치 -> issue body
- 담당자 -> assignee 후보
- 프로젝트 -> 관련 문서/프로젝트 링크
- 기간 -> due 정보 또는 메모
- 관련 코드 -> Related Code 섹션
- 회의 -> Related Docs 섹션

## 브랜치 이름

브랜치는 짧고 의미 있게 만든다.

```text
feature/notion-meeting-tasks
fix/calendar-date-empty
docs/notion-ops-convention
chore/update-dev-env
```

커밋 메시지와 PR 규칙은 `docs/skills/commit-convention/SKILL.md`를 따른다.

## 작업 순서

1. 원본 Notion/문서/회의 내용을 확인한다.
2. 중복 GitHub issue가 있는지 먼저 찾는다.
3. issue draft를 만든다.
4. 관련 문서와 코드 근거를 붙인다.
5. assignee, label, milestone 후보를 제안한다.
6. 사용자가 승인하면 GitHub에 작성한다.
7. 작성 후 Notion 작업이나 문서에 issue 링크를 남긴다.

## 안전 규칙

- 승인 없이 issue, comment, label, milestone을 만들거나 바꾸지 않는다.
- 승인 없이 branch push, PR 생성, merge를 하지 않는다.
- private repo 내용은 권한 없는 곳에 복사하지 않는다.
- 근거가 약하면 `판단 보류`로 둔다.
- 이미 있는 issue가 있으면 새로 만들지 말고 연결 또는 업데이트를 제안한다.

## 응답 방식

먼저 판단을 말한다.
그 다음 바로 복사 가능한 issue draft를 준다.

```text
이건 issue 하나로 충분해.
다만 API 구현과 UI 연결이 섞이면 커질 수 있으니, 인수 기준을 분리해서 적을게.
```
