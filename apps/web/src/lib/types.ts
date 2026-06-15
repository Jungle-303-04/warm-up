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
}

export type BoardView = "kanban" | "week" | "calendar" | "list";

export type CenterTab = "대화" | "보드" | "뷰어";
