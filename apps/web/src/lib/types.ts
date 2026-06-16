// 프론트 전역에서 공유하는 도메인 타입.

// 백엔드 SourceView.kind 와 1:1. "url" 포함.
export type SourceKind = "repo" | "md" | "text" | "pdf" | "url";

export interface SourceKindConfig {
  icon: string;
  label: string;
  chipBg: string;
  chipFg: string;
}

export type StudioArtifactKind = "artifact" | "note";

export interface StudioArtifact {
  id: string;
  kind: StudioArtifactKind;
  title: string;
  typeLabel: string;
  detail: string;
  icon: string;
  tint: string;
  createdAt: number;
  sourceCount: number;
  // 메모 본문(대화 답변을 메모로 저장할 때 사용). 없으면 메타 전용 항목.
  body?: string;
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

// ── RAG 인덱싱 진행(백엔드 SSE 스키마와 1:1) ──────────────────────
// GET /notebooks/{nid}/sources/{sid}/index (1회) 및 .../index/stream(SSE) 응답.
export type IndexStatus = "queued" | "running" | "done" | "failed";
export type IndexFileStatus = "queued" | "indexing" | "done" | "skipped" | "failed";
export type IndexLanguage = "python" | "markdown" | "text" | null;

// 파일 단위 인덱싱 상태. supported=false면 인덱싱 대상에서 제외된다.
export interface IndexFile {
  path: string;
  language: IndexLanguage;
  supported: boolean;
  status: IndexFileStatus;
  chunks: number;
}

// 소스 단위 인덱싱 진행 스냅샷.
export interface IndexProgress {
  source_id: string;
  notebook_id: string;
  status: IndexStatus;
  total_files: number;
  processed_files: number;
  skipped_files: number;
  total_chunks: number;
  indexed_chunks: number;
  percent: number; // 0~100
  files: IndexFile[];
  error: string | null;
  updated_at: string;
  // 최신화(클론/인덱싱) 완료 시각. done일 때만 채워지며 그 외엔 null.
  last_synced_at: string | null;
}

// GET /link-metadata?url=... 응답. 실패해도 200(가능 필드만 채워짐).
export interface LinkMetadata {
  title: string | null;
  description: string | null;
  icon_url: string | null;
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

// 근거 인용(UI 모델). 답변이 참조한 소스 위치를 가리킨다.
export interface Citation {
  sourceId: string; // Source.id
  sourceName: string; // 표시용 소스 이름
  path?: string; // 파일 경로(있으면)
  snippet?: string; // 인용 미리보기
}

export interface NotebookChatCitation {
  source_id: string;
  source_title: string;
  path: string | null;
  snippet: string;
}

export interface NotebookChatResponse {
  answer: string;
  citations: NotebookChatCitation[];
}

export interface NotebookChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: NotebookChatCitation[];
  source_ids: string[] | null;
  created_at: string;
}

export interface NotebookChatMessageList {
  messages: NotebookChatMessage[];
}

// 채팅 UI 메시지 모델(Claude/ChatGPT풍). 화면 렌더의 단일 단위.
// kind=answer: 본문 + 인용칩, notice: 보류/오류 안내 박스.
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  kind: "answer" | "notice";
  citations: Citation[];
  // 새로 도착한 어시스턴트 메시지만 타이핑 효과(기록 복원분은 즉시 표시).
  animate?: boolean;
}

// 중앙 패널 토글: 뷰어 ⇄ 채팅.
export type CenterTab = "대화" | "뷰어";
