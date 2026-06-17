// UI 셸용 공통 표시 데이터.
import type { GeneratableArtifactType, SourceKind, SourceKindConfig } from "./types";
export { fileIconForPath } from "./file-kind";

// 새 소스 종류는 여기에 한 줄만 추가하면 UI 전체에 반영됨
export const SOURCE_KINDS: Record<SourceKind, SourceKindConfig> = {
  repo: { icon: "github", label: "GitHub 저장소", chipBg: "#E1F5EE", chipFg: "#0F6E56" },
  md: { icon: "description", label: "Markdown", chipBg: "#E6F1FB", chipFg: "#185FA5" },
  text: { icon: "text_snippet", label: "텍스트", chipBg: "#F1EFE8", chipFg: "#5F5E5A" },
  pdf: { icon: "picture_as_pdf", label: "PDF", chipBg: "#FCEBEB", chipFg: "#A32D2D" },
  url: { icon: "link", label: "URL", chipBg: "#EFEAFB", chipFg: "#6B3FA0" },
};

// 채팅 추천 질문(목업).
export const SUGGESTIONS = [
  "이 레포의 핵심 실행 흐름을 소스코드 기준으로 설명해줘",
  "최근 커밋에서 실제로 바뀐 파일과 영향도를 요약해줘",
  "문서와 소스코드가 어긋난 부분을 찾아줘",
  "주요 API 라우트와 데이터 모델 관계를 정리해줘",
  "오류가 날 만한 구현 지점과 개선 우선순위를 알려줘",
];

// 스튜디오(우측 패널) 타일. RepoLM 산출물만 유지
// hint = 카드 보조 설명, tint = 카드별 고유 색조(아이콘 박스 배경/글자에 사용).
export interface StudioTile {
  // 생성할 백엔드 산출물 종류(POST /artifacts {type}). note 제외.
  type: GeneratableArtifactType;
  icon: string;
  label: string;
  typeLabel: string;
  hint: string;
  tint: StudioTint;
  beta?: boolean;
  disabledReason?: string;
}

// 카드별 고유 색조 키. globals.css의 .studio-tint-* 클래스와 1:1.
export type StudioTint = "blue" | "violet" | "teal" | "amber" | "rose" | "indigo" | "green" | "cyan";

export const STUDIO_TILES: StudioTile[] = [
  { type: "uml", icon: "account_tree", label: "UML", typeLabel: "UML", hint: "클래스·시퀀스 구조", tint: "blue" },
  { type: "erd", icon: "schema", label: "ERD", typeLabel: "ERD", hint: "데이터 모델 관계", tint: "violet" },
  {
    type: "dependency",
    icon: "hub",
    label: "의존성 그래프",
    typeLabel: "Graph",
    hint: "모듈 연결과 영향권",
    tint: "teal",
    disabledReason: "정확한 모듈 그래프 평가 후 활성화 예정",
  },
  { type: "change_summary", icon: "difference", label: "변경 요약", typeLabel: "Diff", hint: "커밋·파일 변화 압축", tint: "amber" },
];

export const RECOMMENDED_NOTEBOOKS = [
  {
    publisher: "Google Research",
    title: "컴퓨터가 뇌를 시뮬레이션할 수 있을까?",
    date: "2025. 7. 29.",
    sourceCount: 17,
    icon: "public",
    tone: "blue",
  },
  {
    publisher: "The Economist",
    title: "Archive 1945",
    date: "2025. 9. 30.",
    sourceCount: 27,
    icon: "public",
    tone: "yellow",
  },
  {
    publisher: "AI Dev Workspace",
    title: "변화하는 개발 워크플로우",
    date: "2026. 2. 2.",
    sourceCount: 19,
    icon: "notebook",
    tone: "green",
  },
];
