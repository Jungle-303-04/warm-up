// UI 셸용 더미 데이터. 실제 연동 시 서버 응답으로 대체된다.
import type {
  BoardStatus,
  BoardStatusMeta,
  BoardTask,
  Member,
  Source,
  SourceKind,
  SourceKindConfig,
} from "./types";

// 데모 기준 날짜(2026-06). 보드의 "오늘"·기본 커서로 사용해 SSR/CSR 불일치를 피한다.
export const TODAY = new Date(2026, 5, 16);

// 데모(목업) 워크스페이스 멤버. 실제로는 워크스페이스 멤버(GitHub 조직)로 대체된다.
// 로그인 사용자(woonyong-kr)는 화면에서 "나"로 강조된다.
export const MEMBERS: Record<string, Member> = {
  "woonyong-kr": { login: "woonyong-kr", name: "우녕", color: "#0F6E56" },
  minjeong: { login: "minjeong", name: "민정", color: "#185FA5" },
  chanbin: { login: "chanbin", name: "찬빈", color: "#A32D2D" },
};

// 새 소스 종류는 여기에 한 줄만 추가하면 UI 전체에 반영된다.
export const SOURCE_KINDS: Record<SourceKind, SourceKindConfig> = {
  repo: { icon: "folder_code", label: "GitHub 저장소", chipBg: "#E1F5EE", chipFg: "#0F6E56" },
  md: { icon: "description", label: "Markdown", chipBg: "#E6F1FB", chipFg: "#185FA5" },
  text: { icon: "text_snippet", label: "텍스트", chipBg: "#F1EFE8", chipFg: "#5F5E5A" },
  pdf: { icon: "picture_as_pdf", label: "PDF", chipBg: "#FCEBEB", chipFg: "#A32D2D" },
};

const API_README = `# team/api

FastAPI + 헥사고날 아키텍처. 저장소의 **모든 브랜치**를 인덱싱합니다.

## 모듈
- \`app/repo_rag\` — 청킹·임베딩·하이브리드 검색
- \`app/pipeline\` — 동기화 파이프라인
- \`app/auth\` — GitHub OAuth

> 브랜치별 차이는 뷰어에서 비교할 수 있습니다.
`;

const MEETING_TXT = `2026-06 스프린트 회의록

참석: 우녕, 민정
- 인증 미들웨어 401 처리 문서화 필요
- 검색 가중치(벡터:키워드) 튜닝 합의
- 보드 캘린더 뷰 우선순위 상향

결정: 제안→승인→이슈 발행 흐름을 데모에 포함.
`;

const PDF_TEXT = `보안 감사 보고서 (요약)

· 토큰 저장: HttpOnly 쿠키 — 적합
· 의존성 취약점: 0건 (npm audit)
· 권장: 발행 토큰 스코프 최소화

PDF 원본은 추출 텍스트로 인덱싱됩니다.
`;

export const SAMPLE_DOC = `# docs/architecture.md

팀 저장소를 인덱싱해 **근거 기반**으로 답하고 제안하는 워크스페이스입니다.

## 인증 흐름

1. 클라이언트가 \`POST /api/auth/login\` 호출
2. 서버가 자격 증명 검증 후 **HttpOnly JWT 쿠키** 발급
3. 이후 요청은 쿠키의 토큰으로 인증

> 만료 토큰은 인증 미들웨어에서 \`401\`로 처리됩니다.

### 검색 파이프라인

\`\`\`python
def search(query: str) -> list[Chunk]:
    vec = embed(query)
    return store.hybrid_search(vec, query)  # 벡터 + 키워드 융합
\`\`\`

| 단계 | 설명 |
| --- | --- |
| 청킹 | 심볼 단위 + 마크다운 섹션 |
| 임베딩 | OpenAI / 결정론적 |
| 검색 | pgvector 하이브리드 |

자세한 내용은 [README](#)를 참고하세요.
`;

export const SOURCES: Source[] = [
  {
    id: "a",
    name: "team/api",
    kind: "repo",
    progress: 100,
    branches: ["main", "develop", "feat/auth", "feat/search"],
    externalUrl: "https://github.com/team/api",
    content: API_README,
  },
  {
    id: "b",
    name: "team/web",
    kind: "repo",
    progress: 41,
    status: "동기화중",
    branches: ["main", "develop", "feat/ui"],
    externalUrl: "https://github.com/team/web",
    content: "# team/web\n\nNext.js 15 프론트엔드. 동기화 진행 중입니다.\n",
  },
  { id: "c", name: "docs/architecture.md", kind: "md", progress: 100, content: SAMPLE_DOC },
  { id: "d", name: "회의록-2026-06.txt", kind: "text", progress: 100, content: MEETING_TXT },
  {
    id: "e",
    name: "보안감사_보고서.pdf",
    kind: "pdf",
    progress: 72,
    status: "인덱싱중",
    content: PDF_TEXT,
  },
];

export const THREADS = ["인증 흐름 점검", "스프린트 계획", "ERD 리뷰"];

export const SUGGESTIONS = [
  "이 저장소들의 인증 흐름을 요약해줘",
  "최근 브랜치에서 바뀐 핵심 로직은?",
  "문서와 코드가 어긋난 부분을 찾아줘",
];

export const STUDIO_TILES = [
  { icon: "account_tree", label: "UML" },
  { icon: "schema", label: "ERD" },
  { icon: "checklist", label: "계획" },
  { icon: "calendar_month", label: "일정 요약" },
  { icon: "report", label: "보고서" },
  { icon: "mindmap", label: "마인드맵" },
];

export const STUDIO_NOTES = ["도메인 ERD v2", "인증 시퀀스 UML"];

export const BOARD_STATUS_ORDER: BoardStatus[] = ["todo", "doing", "done"];

export const BOARD_STATUS_META: Record<BoardStatus, BoardStatusMeta> = {
  todo: { label: "할 일", dotBg: "#F1EFE8", dotFg: "#5F5E5A" },
  doing: { label: "진행 중", dotBg: "#E6F1FB", dotFg: "#185FA5" },
  done: { label: "완료", dotBg: "#E1F5EE", dotFg: "#0F6E56" },
};

// RepoLM 라벨이 붙은 이슈(보드↔GitHub 단방향)를 표현하는 데모 태스크.
// author = 작성자/담당자 handle(MEMBERS). 팀 도구이므로 항목마다 작성자가 보인다.
export const BOARD_TASKS: BoardTask[] = [
  { id: "t1", title: "토큰 만료 401 문서화", status: "todo", due: "2026-06-16", repo: "team/api", author: "woonyong-kr" },
  { id: "t2", title: "ERD v2 리뷰 반영", status: "todo", due: "2026-06-18", repo: "team/api", author: "minjeong" },
  { id: "t3", title: "온보딩 링크 점검", status: "todo", due: "2026-06-22", repo: "team/web", author: "chanbin" },
  { id: "t4", title: "인증 미들웨어 리팩터", status: "doing", due: "2026-06-16", repo: "team/api", author: "woonyong-kr" },
  { id: "t5", title: "검색 가중치 튜닝", status: "doing", due: "2026-06-17", repo: "team/api", author: "minjeong" },
  { id: "t6", title: "PDF 인덱싱 파이프라인", status: "doing", due: "2026-06-19", repo: "team/web", author: "chanbin" },
  { id: "t7", title: "OAuth 콜백 안정화", status: "done", due: "2026-06-15", repo: "team/api", author: "woonyong-kr" },
  { id: "t8", title: "다크/라이트 토큰 정리", status: "done", due: "2026-06-12", repo: "team/web", author: "minjeong" },
  { id: "t9", title: "월말 회고 준비", status: "todo", due: "2026-06-30", repo: "team/web", author: "chanbin" },
];
