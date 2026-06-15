# RepoLM 팀 공유/가시성 모델

팀 단위 도구로서 "누가 무엇을 소유하고 어디까지 팀에 보이는가"를 정의한다.
레퍼런스: Notion(Teamspace/Private), GitHub(org→repo 권한·Issues/Projects),
Google·Notion Calendar(개인+팀 레이어), Claude Team(지식 공유·대화 개인 기본).

## 공유 매트릭스

| 표면 | 공유 단위 | 차용 모델 | 식별/표시 |
|---|---|---|---|
| **소스**(저장소·문서) | 워크스페이스 전체 공유 | GitHub org repos · Notion Teamspace | 연결한 사람(connected by) + 인덱싱 상태 |
| **보드**(태스크/제안) | 팀 공유 | GitHub Projects/Issues | 작성자 + 담당자(assignee) + 라벨 |
| **대화** | 개인 기본 · 선택적 공유 | Claude Team · Notion private→share | 소유자 + 공유 시 "팀 공개" 배지 |
| **질의 범위**(선택 소스) | 개인·대화 단위 | (각자 질문 범위가 다름) | — |

## 권한 — 2축 (혼동 금지)

권한은 **독립된 두 축**으로 나눈다. 진실 공급원이 다르다.

- **가시성 = GitHub** : 사용자는 자신이 GitHub에서 접근 가능한 repo의 소스·보드만 본다.
  규칙 `required_repos ⊆ member.accessible_repos`. `accessible_repos`는 OAuth 토큰으로 조회,
  **4h 캐시 + 로그인 시 갱신**. (비공개 repo 노출 사고 방지의 핵심)
- **쓰기 = 워크스페이스 역할** : 아래 표. 의존성 `require_write`로 게이트.

| 역할 | 소스 연결 | 태스크/제안·발행 | 대화 | 멤버 초대 |
|---|---|---|---|---|
| Owner | ✅ | ✅ | ✅ | ✅ |
| Member(쓰기) | ✅ | ✅ | ✅ | ❌ |
| Viewer(읽기) | ❌ | ❌ | 읽기 + **본인 개인 대화 생성은 허용** | ❌ |

> 개인 대화는 "공용 자원"이 아니므로 쓰기 게이트의 예외다. 소스 연결·발행·태스크만 막는다.

## 대화 공유

- **기본 = 개인.** 작성자만 본다.
- "**팀 공유**" 버튼 → 워크스페이스 멤버에게 읽기 공개(배지 표시). (Claude Team/Notion 방식)
- 공유해도 질의 범위(선택 소스)는 대화에 저장된 그대로 보인다.

## 소스 종류 (D3/D4)

- **GitHub 레포**(모든 브랜치 인덱싱) + **직접 업로드(md/txt/pdf)**. "+ 소스 추가" = 레포 연결 / 파일 업로드 2-탭(웹검색 제외).
- 가시성: 레포=GitHub 접근권(2축), 업로드=워크스페이스 멤버 전체.

## GitHub 저장소를 소스로 연결

- 인덱싱 범위 = **repo의 모든 추적 텍스트 파일(코드+문서)**. 문서만 받지 않는다 —
  제품 핵심 가치(문서↔코드 어긋남 탐지)가 둘 다 필요.
- 뷰어 = **인덱싱된 파일의 폴더 트리** + 파일 렌더(`.md`→마크다운, 코드→읽기전용 하이라이트,
  인용은 `파일:라인` 점프). "문서만" 필터 토글.
- **풀 Git 브라우저(브랜치 diff·blame 등)는 만들지 않는다** — GitHub의 일이고 에러원.
  "전체 보기"는 GitHub로 링크 위임(외부 열기).
- 결론: **소스코드 트리 O(경량 읽기), IDE X.**

## 보드 = GitHub 미러 + 로컬 태스크 (D5)

- 보드는 두 출처를 합쳐 표시. 태스크 `origin ∈ {github_issue, local}`로 구분(배지).
  - **`github_issue`**: 연결 repo의 `RepoLM` 라벨 이슈 **읽기 미러**(read-only, SSOT=GitHub).
  - **`local`**: RepoLM 자체 태스크. **쓰기 가능(역할 게이트)**. 승인된 제안 → local 태스크 자동 생성.
- GitHub로의 쓰기는 **제안 승인 → 이슈 발행**으로만(`POST /github/proposals/{id}/publish`).
  로컬 태스크는 GitHub와 동기화하지 않는다(현 단계) → 양방향 충돌 0.

## 데모 반영 방식

- 모든 공유 항목에 **작성자 아바타 + 시간**(식별 문제 해결).
- 소스/보드 = "팀 공유" 배지, 대화 = "개인" 잠금 아이콘 + "팀 공유" 토글.
- 역할별 비활성("준비 중" 대신 "Viewer는 불가" 등 의미 있는 상태).
- 보드는 GitHub Issue 미러 톤(라벨·이슈번호·작성자), 로컬 편집 UI 없음.

## 백엔드 매핑 (현재 vs 신규)

- 이미 됨: 소스 sync·검색, 제안 생성/승인/발행, OAuth 로그인/토큰, 제안 LangGraph(생성).
- 신규 필요:
  - 워크스페이스/멤버·역할 모델 + `require_write` + `accessible_repos`(GitHub, 4h 캐시).
  - 대화 영속화+공유 플래그 + **`scope_source_ids`(질의 범위)를 대화에 저장**.
  - **답변 생성 그래프**(retrieve→pack→answer→groundedness/abstain) — 현재 retrieve까지만.
  - 인덱싱 파일 트리/본문 조회(`GET /pipeline/repositories/{id}/files[/{path}]`, **원문 스냅샷·기본 브랜치**).
  - 보드용 GitHub Issues 읽기 프록시(워크스페이스 멀티레포 집계 + 캐시).
  - 작성자 표현 통일 `author = {login, avatar_url}`(소스·제안·대화·보드 공통).
