# RepoLM 결정 로그 (단일 진실 공급원)

문서 간 모순이 생기면 **이 파일이 우선**한다. 모든 결정은 날짜·상태와 함께 기록한다.
team-sharing-model / backend-handoff / frontend-handoff / langgraph-agent-design 는 이 결정을 따른다.

## 확정 결정 (2026-06-16)

| # | 주제 | 결정 | 영향 |
|---|---|---|---|
| D1 | 목표 수준 | **실서비스 MVP** | 실데이터·권한 2축·영속화·보드 미러까지 실제 동작. 목업은 단계적 제거. |
| D2 | 테마 | **시스템(다크 기본 + 토글)**, Tailwind만 | 다크를 1급으로. `.dark`/`.light` 토큰 + 토글 복구. 진짜 NotebookLM 톤. |
| D3 | 소스 종류 | **레포 + 직접 업로드(md/txt/pdf)** | 백엔드: 업로드 소스 인덱싱 경로 추가. 프론트 md/txt/pdf 타입 정당화. |
| D4 | 소스 추가 UX | **레포 연결 + 파일 업로드(웹검색 제외)** | "+ 소스 추가" = 레포 URL 연결 / 파일 업로드 2-탭 모달. 웹검색 미포함. |
| D5 | 보드 정체성 | **둘 다(GitHub 미러 + 로컬 태스크)** | 보드 = RepoLM 라벨 이슈 읽기 미러 ∪ 로컬 태스크. 로컬은 쓰기(역할). 출처 배지로 구분. |
| D6 | 스튜디오 | **혼합: UML/ERD/계획 + 보고서/마인드맵** | 개발 산출물 + NotebookLM식 생성물 일부. 생성은 LLM 그래프. |
| D7 | 채팅 답변 범위 | **lookup + locate + summarize** | 답변 그래프 1차 = 이 3개 의도. consistency/planning/change는 후속. |
| D8 | planning 위치 | **둘 다(채팅 답변 + 보드 액션)** | 일정 제안을 채팅 `schedule` kind로도, 보드 액션으로도. |

## 파생 규칙 (모순 제거용)

- **소스 모델**: `kind ∈ {repo, md, text, pdf}`. repo=GitHub 연결(모든 브랜치), 나머지=업로드.
  가시성: repo는 GitHub 접근권(2축), 업로드는 워크스페이스 멤버 전체.
- **보드 태스크 출처**: `origin ∈ {github_issue, local}`. github_issue=읽기전용 미러, local=쓰기(역할).
  승인된 제안 → local 태스크 자동 생성(기존 동작 유지). GitHub 발행은 별개(이슈 코멘트).
- **테마**: 기본 시스템(prefers-color-scheme), 토글로 light/dark/system. 색은 토큰으로만.
- **권한 2축 유지**: 가시성=GitHub(`required_repos ⊆ accessible_repos`), 쓰기=역할(`require_write`).

## 확정 결정 (2026-06-16, 2차)

| # | 주제 | 결정 |
|---|---|---|
| O1 | 업로드 제한 | **md/txt/pdf만 + 10MB 상한**. 그 외 타입 거부. |
| O2 | 보드 로컬↔GitHub | **동기화 없음**(로컬 태스크는 RepoLM 내부, GitHub 쓰기는 제안 발행만). |
| O3 | 테마 기본 | **시스템 따름**(prefers-color-scheme) + light/dark/system 토글. |

## 열린 결정 (다음 사이클에 질문)

- 답변 스트리밍 도입 시점.
- 스튜디오 생성물(보고서/마인드맵)의 정확한 산출 포맷.

## 반복 루프 프로토콜

1. 이 파일의 "열린 결정"에서 블로킹 3~4개를 사용자에게 질문 → 확정 결정으로 이동.
2. 결정을 문서·코드에 반영(모순 제거).
3. `bash scripts/verify.sh`(tsc+pytest+ruff+build) 녹색 확인.
4. 작업 단위 커밋 → 백로그 갱신. (1사이클 = 대화 한 턴)
