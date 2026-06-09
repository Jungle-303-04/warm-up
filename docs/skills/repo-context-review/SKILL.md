---
name: repo-context-review
description: Use when checking whether a document, Notion item, meeting note, spec, or task matches the current repository implementation; inspect code and docs, cite file paths, and classify what is verified, stale, missing, or uncertain.
---

# Repo Context Review

## 기준

문서와 회의 내용은 실제 레포 구현과 맞아야 의미가 있다.
추측으로 맞다고 하지 않는다.
파일을 보고 판단한다.

이 스킬은 문서, Notion 항목, 회의록, 작업, 스펙이 현재 레포와 맞는지 확인할 때 쓴다.

## 확인 순서

1. 사용자가 준 주장, 문서, 작업 내용을 작은 항목으로 나눈다.
2. 관련 키워드를 `rg`로 찾는다.
3. 실제 구현 파일, 설정 파일, 테스트, 문서를 같이 본다.
4. 각 항목을 `검증됨`, `낡음`, `구현 없음`, `판단 보류`로 나눈다.
5. 근거 파일 경로와 필요한 경우 라인 번호를 남긴다.
6. 문서 수정이 필요하면 최소 범위로 제안하거나 직접 수정한다.

## 판정 기준

- `검증됨`: 현재 코드나 설정에서 확인된다.
- `낡음`: 문서 내용은 있지만 현재 코드와 다르다.
- `구현 없음`: 문서에는 있지만 레포에서 구현 근거를 못 찾았다.
- `판단 보류`: 이름이 다르거나 외부 시스템 정보가 필요하다.

## 봐야 하는 것

- `README.md`
- `docs/`
- `package.json`, `pnpm-workspace.yaml`
- `backend/pyproject.toml`
- `compose.yaml`
- `apps/`, `backend/`, 설정 파일
- 테스트 파일과 실행 스크립트

## 응답 방식

판단을 먼저 말한다.
그 다음 근거를 짧게 붙인다.

좋은 형태:

```text
판단: 문서의 RAG worker 설명은 일부 낡았어.

- 검증됨: Docker Compose에 backend 서비스는 있음
- 낡음: 문서에는 worker가 분리돼 있다고 되어 있지만 현재 compose에는 별도 worker 없음
- 수정 필요: 13-minimal-pipeline-plan.md의 worker 실행 설명
```

## 주의

- 코드 근거 없이 확정하지 않는다.
- 문서가 맞고 코드가 부족할 수도 있으니 바로 문서를 지우지 않는다.
- 외부 GitHub, Notion, 배포 상태는 현재 레포만으로 확정하지 않는다.
- 수정할 때는 문서의 목적을 유지하고 필요한 문장만 바꾼다.
