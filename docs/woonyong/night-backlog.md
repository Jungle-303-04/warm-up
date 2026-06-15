# 야간 자동화 — 태스크 보드 + 에이전트 상태

자동화 에이전트의 **단일 상태/태스크 소스**. 한 실행 = 한 항목. 위에서부터.
상태: `[ ]` 대기 · `[~]` 진행중(시작 시 표시) · `[x]` 완료 · `[!]` 블록(에러/모호).
완료 기준: **tsc green + 커밋 성공**. 결정 기준 = `decisions.md`(D1~D8, O1~O3).

## 에이전트 상태 (매 실행 시 갱신)
- last_run: 2026-06-16T02:00:00Z
- last_result: DONE
- in_progress: (없음)

## 태스크 (잘게)

### 리팩터(공용 헬퍼 흡수 — 중복 제거, 동작 동일)
- [x] N1. 다크 테마 + 토글 (완료)
- [x] R1. `board-panel`: 로컬 날짜유틸 제거 → `lib/date` 사용. 로컬 MemberAvatar 제거 → `ui/avatar`(`<Avatar member=.../>`).
- [x] R2. `proposal-card`: `isoToday` 인라인 제거 → `lib/date`의 `isoDate(TODAY)` 사용.
- [x] R3. `center-panel`: 패널 래퍼 → `ui/panel`, 탭 분기 className → `lib/cn`.
- [x] R4. `studio-panel`: 패널 래퍼 → `ui/panel`.

### 스튜디오 혼합 타일(D6)
- [ ] S1. `fixtures.STUDIO_TILES`에 "보고서","마인드맵" 추가. 필요 아이콘은 `icon.tsx`에 매핑 추가(report→description, mindmap→account_tree 등 lucide). 타일 클릭=준비 중 유지.

### 소스 추가 모달(D4) — 목업
- [ ] M1. `components/ui/modal.tsx` 생성: 접근성 다이얼로그(role="dialog" aria-modal, 오버레이, Esc 닫기, position:fixed 금지—인플로우 오버레이). 재사용 가능.
- [ ] M2. `components/source-add-modal.tsx`: 2-탭(①GitHub 레포 URL ②파일 업로드 md/txt/pdf·10MB 안내). 목업(제출=닫기). `sources-panel`의 "소스 추가" 버튼을 이 모달 열도록(준비중 해제, 상태는 로컬 useState).

### GitHub 신원(F1)
- [ ] I1. `auth-menu`: 로그인 사용자 아이콘 → 실제 사진 `https://avatars.githubusercontent.com/u/${me.user_id}` (plain img, rounded-full).
- [ ] I2. `fixtures.SOURCE_KINDS.repo.icon` → `"github"`(인라인 SVG 아이콘 사용).

### 채팅 답변 골격(D7) — 목업
- [ ] A1. `lib/types.ts`에 `AgentResponse` 판별유니온(kind: answer/references/summary/abstain/clarify) + `Citation` 타입 추가.
- [ ] A2. `chat-view`: 예시 답변을 `AgentResponse` 목업으로 바꾸고 kind별 렌더 스텁(answer=본문+인용칩, references=파일목록, summary=문단, abstain/clarify=안내). 백엔드 연결 지점 주석.

## 규칙
1. 한 실행 = 1개. 시작 시 `[~]`, 끝 `[x]`/`[!]`.
2. **반드시 `tsc` green**. 아니면 변경 되돌리고 `[!]` + night-log에 사유.
3. **반드시 `bash scripts/auto-commit.sh "<msg>"` 로 커밋**(매 사이클). push 금지.
4. 추상화/가독성 최우선: 중복은 공용 헬퍼(`lib/cn`,`lib/date`,`ui/*`)로. 새 중복 만들지 말 것.
5. 프론트·목업만. 백엔드/실API/의존성설치/rm/push/`git add -A` 금지.
6. 모호하면 구현 말고 `[!]` + night-log에 `QUESTION:`.
