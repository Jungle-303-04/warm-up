# 야간 자동화 백로그 (프론트 전용, 목업 안전)

자동화는 **한 번에 하나만**, 위에서부터 처리한다. 각 항목은 tsc(+build) green이어야 유지.
결정 기준은 `decisions.md`(D1~D8, O1~O3). 백엔드 호출/실데이터는 건드리지 않는다(목업 유지).
실패하면 그 항목 변경을 되돌리고 `night-log.md`에 BLOCKED로 기록 후 중단.

## 순서

- [x] N1. 다크 테마 + 시스템/라이트/다크 토글 (D2/O3) — globals 다크 토큰, 부트스트랩, ThemeToggle.
- [ ] N2. 공용 모듈 리팩터 마무리 — board-panel/proposal-card는 `lib/date`, board는 `ui/avatar`,
      center-panel/studio-panel은 `ui/panel`, top-bar 알림버튼은 `ui/icon-button`로 치환(중복 제거). 동작 동일.
- [ ] N3. 스튜디오 혼합 타일 (D6) — 기존 UML/ERD/계획/일정에 "보고서", "마인드맵" 타일 추가(목업, 클릭=준비 중).
- [ ] N4. 소스 추가 모달 (D4) — "+ 소스 추가" 클릭 시 2-탭 모달: ①GitHub 레포 URL 연결 ②파일 업로드(md/txt/pdf, 10MB 안내).
      목업(제출 시 토스트/닫기만). 접근성(역할=dialog, esc 닫기).
- [ ] N5. 작성자 신원 마감 (F1) — auth-menu 아바타를 실제 GitHub 사진(`avatars.githubusercontent.com/u/{user_id}`),
      repo 소스 아이콘 `SOURCE_KINDS.repo.icon`을 `"github"`로.
- [ ] N6. AgentResponse 타입 + kind 렌더 골격 (D7) — `lib/types.ts`에 `AgentResponse`(answer/references/summary/...)
      추가, chat-view에 kind별 렌더 스텁(목업 데이터). 백엔드 연결 지점만 준비.

## 규칙

1. 한 사이클 = 백로그 1개. 작게.
2. `cd apps/web && ./node_modules/.bin/tsc --noEmit` green 필수. 가능하면 `pnpm build`도.
3. 디자인/사용성: 진짜 NotebookLM 톤(다크 기본), Tailwind 유틸만, 토큰만 사용.
4. 끝나면 항목 [x] 체크 + `night-log.md`에 1줄 기록. 커밋 시도(잠기면 변경만 남김).
5. 결정이 필요한 모호함이 생기면 구현 말고 `night-log.md`에 QUESTION으로 적고 다음 항목으로.
