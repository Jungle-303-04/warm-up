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
// hint = 카드 보조 설명, tint = 카드별 고유 색조(아이콘 박스 배경/글자에 사용).
export interface StudioTile {
  icon: string;
  label: string;
  hint: string;
  tint: StudioTint;
  beta?: boolean;
}

// 카드별 고유 색조 키. globals.css의 .studio-tint-* 클래스와 1:1.
export type StudioTint = "blue" | "violet" | "teal" | "amber" | "rose" | "indigo" | "green" | "cyan";

// 스튜디오 상단 와이드 히어로 카드(가장 강조되는 산출물).
export const STUDIO_HERO = {
  icon: "code_tour",
  tint: "teal" as StudioTint,
  label: "코드 투어",
  hint: "핵심 경로를 따라가는 단계별 가이드",
  meta: "소스 기반 · 베타",
};

export const STUDIO_TILES: StudioTile[] = [
  { icon: "account_tree", label: "UML", hint: "클래스·시퀀스 다이어그램", tint: "blue" },
  { icon: "schema", label: "ERD", hint: "데이터 모델 관계도", tint: "violet" },
  { icon: "dependency", label: "의존성 그래프", hint: "모듈 의존 관계", tint: "amber" },
  { icon: "report", label: "보고서", hint: "근거 기반 문서", tint: "rose" },
  { icon: "mindmap", label: "마인드맵", hint: "개념 연결도", tint: "indigo" },
  { icon: "diff", label: "변경 요약", hint: "커밋·diff 정리", tint: "green", beta: true },
  { icon: "test_map", label: "테스트맵", hint: "커버리지 매핑", tint: "cyan" },
  { icon: "audio", label: "오디오 개요", hint: "대화형 요약 음성", tint: "blue", beta: true },
];

// 메모 데모: 제목 + 종류(서브텍스트) + 시간 + 아이콘.
export const STUDIO_NOTES = [
  { title: "도메인 ERD v2", kind: "ERD", time: "2시간 전", icon: "schema" },
  { title: "인증 시퀀스 UML", kind: "UML", time: "어제", icon: "account_tree" },
];

// 채팅 상단 요약 카드(목업). NotebookLM처럼 생성된 듯한 개요.
// segs = 키워드 강조용 세그먼트 배열(bold=true면 굵게).
export const CHAT_SUMMARY: { seg: string; bold?: boolean }[] = [
  { seg: "연결된 저장소는 " },
  { seg: "FastAPI 백엔드", bold: true },
  { seg: "와 " },
  { seg: "Next.js 프런트엔드", bold: true },
  { seg: "로 구성되며, 인증은 " },
  { seg: "JWT 미들웨어", bold: true },
  { seg: "를 거쳐 처리됩니다. 문서에는 아키텍처 개요와 " },
  { seg: "데이터 모델", bold: true },
  { seg: "이 정리되어 있어 코드와 대조해 어긋난 지점을 빠르게 짚어낼 수 있습니다." },
];
