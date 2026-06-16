// UI 셸용 더미 데이터. 채팅 답변·스튜디오는 아직 목업이라 여기서 데이터를 가져온다.
import type { AgentResponse, SourceKind, SourceKindConfig } from "./types";

// 새 소스 종류는 여기에 한 줄만 추가하면 UI 전체에 반영된다.
export const SOURCE_KINDS: Record<SourceKind, SourceKindConfig> = {
  repo: { icon: "github", label: "GitHub 저장소", chipBg: "#E1F5EE", chipFg: "#0F6E56" },
  md: { icon: "description", label: "Markdown", chipBg: "#E6F1FB", chipFg: "#185FA5" },
  text: { icon: "text_snippet", label: "텍스트", chipBg: "#F1EFE8", chipFg: "#5F5E5A" },
  pdf: { icon: "picture_as_pdf", label: "PDF", chipBg: "#FCEBEB", chipFg: "#A32D2D" },
  url: { icon: "link", label: "URL", chipBg: "#EFEAFB", chipFg: "#6B3FA0" },
};

// 채팅 추천 질문(목업).
export const SUGGESTIONS = [
  "이 소스들의 인증 흐름을 요약해줘",
  "최근 브랜치에서 바뀐 핵심 로직은?",
  "문서와 코드가 어긋난 부분을 찾아줘",
];

// 채팅 답변 데모(D7). 실제 연동 시 백엔드 답변 그래프 출력으로 대체된다.
export const DEMO_RESPONSE: AgentResponse = {
  kind: "answer",
  text: "로그인 실패는 JWT 만료가 가장 흔한 원인입니다. 인증 미들웨어가 만료 토큰을 401로 처리합니다.",
  citations: [
    { sourceId: "a", sourceName: "team/api", path: "api/auth.py", lines: [12, 18] },
    { sourceId: "c", sourceName: "docs/architecture.md", path: "docs/auth.md" },
  ],
};

// 스튜디오(우측 패널) 데모 타일/메모. 모두 "준비 중".
export const STUDIO_TILES = [
  { icon: "account_tree", label: "UML" },
  { icon: "schema", label: "ERD" },
  { icon: "checklist", label: "계획" },
  { icon: "calendar_month", label: "일정 요약" },
  { icon: "report", label: "보고서" },
  { icon: "mindmap", label: "마인드맵" },
];

export const STUDIO_NOTES = ["도메인 ERD v2", "인증 시퀀스 UML"];
