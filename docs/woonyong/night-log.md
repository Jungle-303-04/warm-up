# 야간 자동화 로그
DONE: R1 board-panel - 로컬 날짜유틸/MemberAvatar 제거, lib/date·ui/avatar 재사용 (tsc green) [2026-06-15T19:21:31Z]
DONE: R2 - proposal-card isoToday 인라인 제거, lib/date의 isoDate(TODAY)로 대체 (tsc green)
DONE: R3 - center-panel 셸을 ui/Panel로 교체, 탭 분기 className을 lib/cn으로 통일 (tsc green)
DONE: R4 - studio-panel aside 셸을 ui/Panel(as="aside")로 교체, 중복 카드 클래스 제거 (tsc green)
DONE: S1 - 스튜디오 타일에 보고서(report→NotebookText)·마인드맵(mindmap→Network) 추가, 클릭=준비중 유지, tsc green
DONE: M1 - 재사용 접근성 Modal(ui/modal.tsx) 추가: role=dialog/aria-modal, absolute inset-0 인플로우 오버레이, Esc·오버레이 닫기, close 아이콘(X) 매핑 (tsc green) [2026-06-15T19:51:05Z]
DONE: M2 source-add-modal - GitHub레포URL/파일업로드 2-탭 접근성 모달(목업, 제출=닫기), sources-panel '소스 추가' 버튼 연결(준비중 해제, 로컬 useState)
DONE: I1 auth-menu - 로그인 사용자 아이콘을 실제 GitHub 아바타 img(rounded-full)로 교체 (tsc green)
DONE: I2 - SOURCE_KINDS.repo.icon을 "folder_code"→"github"로 변경(icon.tsx 인라인 SVG 마크 사용) (tsc green)
DONE: A1 - lib/types.ts에 AgentResponse 판별유니온(answer/references/summary/abstain/clarify)+Citation 타입 추가, tsc green
