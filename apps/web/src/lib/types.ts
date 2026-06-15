// 프론트 전역에서 공유하는 도메인 타입.

export type SourceKind = "repo" | "md" | "text" | "pdf";

export interface SourceKindConfig {
  icon: string;
  label: string;
  chipBg: string;
  chipFg: string;
}

export interface Source {
  id: string;
  name: string;
  kind: SourceKind;
  progress: number;
  status?: string;
  branches?: string[]; // repo 전용: 인덱싱된 모든 브랜치
  externalUrl?: string; // repo/link: 외부에서 열기
  content?: string; // md/text/pdf: 뷰어 본문(추출 텍스트)
}

// 백엔드 계약과 동일한 작성자 표현(team-sharing-model.md). 모든 작성자/담당자 표시의 기준.
export interface Author {
  login: string; // GitHub login
  avatar_url?: string; // 있으면 실제 아바타, 없으면 이니셜 폴백
}

// 워크스페이스 멤버(데모). Author + 로컬 표시용(name/이니셜 색).
export interface Member extends Author {
  name: string;
  color: string; // avatar_url 없을 때 이니셜 배경
}

export type BoardStatus = "todo" | "doing" | "done";

export interface BoardStatusMeta {
  label: string;
  dotBg: string;
  dotFg: string;
}

export interface BoardTask {
  id: string;
  title: string;
  status: BoardStatus;
  due: string; // YYYY-MM-DD
  repo: string;
  author?: string; // 작성자/담당자 login (Member.login). 없으면 담당자 미지정
}

export type BoardView = "kanban" | "week" | "calendar" | "list";

export type CenterTab = "대화" | "보드" | "뷰어";
