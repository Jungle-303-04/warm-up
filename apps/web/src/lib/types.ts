// 프론트 전역에서 공유하는 도메인 타입.

// 백엔드 SourceView.kind 와 1:1. "url" 포함.
export type SourceKind = "repo" | "md" | "text" | "pdf" | "url";

export interface SourceKindConfig {
  icon: string;
  label: string;
  chipBg: string;
  chipFg: string;
}

// 백엔드 NotebookView.
export interface Notebook {
  id: string;
  title: string;
  summary: string | null;
  source_count: number;
  created_at: string;
  updated_at: string;
}

// 백엔드 SourceView.
export interface Source {
  id: string;
  notebook_id: string;
  kind: SourceKind;
  title: string;
  url: string | null;
  repository_url: string | null;
  branch: string | null;
  created_at: string;
}

// 백엔드 SourceDetailView = SourceView + content.
export interface SourceDetail extends Source {
  content: string | null;
}

// 백엔드 NotebookDetailView = NotebookView + sources.
export interface NotebookDetail extends Notebook {
  sources: Source[];
}

// repo 소스 파일 트리 노드.
export interface TreeNode {
  name: string;
  path: string;
  type: "dir" | "file";
  children?: TreeNode[];
}

// 소스 생성 요청 바디.
export interface SourceCreate {
  kind: SourceKind;
  title: string;
  content?: string;
  url?: string;
  repository_url?: string;
  branch?: string;
}

// 채팅 답변 골격(D7: lookup + locate + summarize). 백엔드 답변 그래프 출력과 1:1 대응.

// 근거 인용. 답변이 참조한 소스 위치를 가리킨다.
export interface Citation {
  sourceId: string; // Source.id
  sourceName: string; // 표시용 소스 이름
  path?: string; // 파일 경로(있으면)
  lines?: [number, number]; // [시작, 끝] 줄 범위
  snippet?: string; // 인용 미리보기
  externalUrl?: string; // 외부에서 열기
}

// 답변 그래프의 판별 유니온. kind로 렌더를 분기한다.
export type AgentResponse =
  | { kind: "answer"; text: string; citations: Citation[] } // lookup: 본문 + 인용칩
  | { kind: "references"; intro?: string; citations: Citation[] } // locate: 파일/위치 목록
  | { kind: "summary"; text: string; citations?: Citation[] } // summarize: 문단 요약
  | { kind: "abstain"; reason: string } // 근거 부족 등으로 답변 보류
  | { kind: "clarify"; question: string }; // 추가 정보 요청

// 중앙 패널 토글: 뷰어 ⇄ 채팅.
export type CenterTab = "대화" | "뷰어";
