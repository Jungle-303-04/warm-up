// UI 셸용 공통 표시 데이터.
import type { GeneratableArtifactType, SourceKind, SourceKindConfig } from "./types";

// 새 소스 종류는 여기에 한 줄만 추가하면 UI 전체에 반영된다.
export const SOURCE_KINDS: Record<SourceKind, SourceKindConfig> = {
  repo: { icon: "github", label: "GitHub 저장소", chipBg: "#E1F5EE", chipFg: "#0F6E56" },
  md: { icon: "description", label: "Markdown", chipBg: "#E6F1FB", chipFg: "#185FA5" },
  text: { icon: "text_snippet", label: "텍스트", chipBg: "#F1EFE8", chipFg: "#5F5E5A" },
  pdf: { icon: "picture_as_pdf", label: "PDF", chipBg: "#FCEBEB", chipFg: "#A32D2D" },
  url: { icon: "link", label: "URL", chipBg: "#EFEAFB", chipFg: "#6B3FA0" },
};

// 파일 경로/확장자 → 또렷한 Icon name. NotebookLM처럼 유형이 한눈에 보이게.
// 소스 행·인용칩·뷰어 헤더가 공유한다(중복 매핑 제거의 단일 출처).
const EXT_ICON_MAP: Record<string, string> = {
  // 문서
  md: "description",
  markdown: "description",
  mdx: "description",
  txt: "text_snippet",
  rst: "text_snippet",
  pdf: "picture_as_pdf",
  // 설정/데이터(json/yaml은 중괄호 톤)
  json: "file_json",
  jsonc: "file_json",
  yml: "file_json",
  yaml: "file_json",
  toml: "file_json",
  ini: "file_json",
  cfg: "file_json",
  env: "file_json",
  csv: "file_spreadsheet",
  tsv: "file_spreadsheet",
  // 셸 스크립트
  sh: "file_terminal",
  bash: "file_terminal",
  zsh: "file_terminal",
  // 이미지/벡터
  svg: "file_image",
  png: "file_image",
  jpg: "file_image",
  jpeg: "file_image",
  gif: "file_image",
  webp: "file_image",
};

// 코드로 취급해 file_code 아이콘을 줄 확장자(py 등). EXT_ICON_MAP에 없을 때만 적용.
const CODE_EXTS = new Set([
  "py", "pyi", "ipynb",
  "js", "jsx", "mjs", "cjs", "ts", "tsx",
  "go", "rs", "java", "kt", "kts", "c", "h", "cpp", "cc", "hpp", "cs",
  "rb", "php", "swift", "scala", "dart", "lua", "r", "sql", "html", "htm",
  "xml", "css", "scss", "less", "vue", "svelte",
]);

// 파일 경로 → 표시 아이콘 이름. 확장자 우선, 코드 확장자는 file_code, 그 외 일반 file.
// 확장자 없는 Dockerfile/Makefile 등도 코드 아이콘으로 또렷하게.
export function fileIconForPath(path?: string | null): string {
  if (!path) return "file";
  const name = path.toLowerCase().split("/").pop() ?? "";
  if (name === "dockerfile" || name === "makefile" || name.endsWith(".dockerfile")) {
    return "file_code";
  }
  const ext = name.includes(".") ? name.split(".").pop()! : "";
  if (ext in EXT_ICON_MAP) return EXT_ICON_MAP[ext];
  if (CODE_EXTS.has(ext)) return "file_code";
  return "file";
}

// 채팅 추천 질문(목업).
export const SUGGESTIONS = [
  "이 소스들의 인증 흐름을 요약해줘",
  "최근 브랜치에서 바뀐 핵심 로직은?",
  "문서와 코드가 어긋난 부분을 찾아줘",
];

// 스튜디오(우측 패널) 타일. RepoLM 산출물만 남긴다.
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
}

// 카드별 고유 색조 키. globals.css의 .studio-tint-* 클래스와 1:1.
export type StudioTint = "blue" | "violet" | "teal" | "amber" | "rose" | "indigo" | "green" | "cyan";

export const STUDIO_TILES: StudioTile[] = [
  { type: "uml", icon: "account_tree", label: "UML", typeLabel: "UML", hint: "클래스·시퀀스 구조", tint: "blue" },
  { type: "erd", icon: "schema", label: "ERD", typeLabel: "ERD", hint: "데이터 모델 관계", tint: "violet" },
  { type: "dependency", icon: "hub", label: "의존성 그래프", typeLabel: "Graph", hint: "모듈 연결과 영향권", tint: "teal" },
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
