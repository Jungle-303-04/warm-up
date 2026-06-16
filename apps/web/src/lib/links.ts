// 마크다운 본문 링크 해석 유틸. 뷰어 내부 열람으로 치환하기 위한 분류·경로 정규화.

export type ResolvedLink =
  | { type: "external"; href: string } // 다른 도메인 절대 URL → 새 탭
  | { type: "anchor"; hash: string } // #heading → 페이지 내 스크롤
  | { type: "repo-file"; path: string } // 같은 repo의 파일 → openFile
  | { type: "ignore" }; // 매핑 불가(mailto, 미지원 등) → 무시

// 절대 http(s) URL 여부.
function isAbsoluteHttp(href: string): boolean {
  return /^https?:\/\//i.test(href);
}

// repo 루트 기준으로 상대 경로를 정규화한다.
// baseFilePath: 현재 보고 있는 파일 경로(예: "docs/guide/intro.md"). 없으면 루트 기준.
// target: 링크의 상대/루트 경로(예: "./api.md", "../x.md", "/docs/y.md").
// 반환: repo 루트 기준 정규화 경로(앞에 "/" 없음). 범위를 벗어나면 null.
export function resolveRepoPath(baseFilePath: string | undefined, target: string): string | null {
  // 쿼리/해시는 파일 경로 해석에서 제거(파일 내부 앵커는 별도 처리).
  const clean = target.split("#")[0].split("?")[0];
  if (!clean) return null;

  let segments: string[];
  if (clean.startsWith("/")) {
    // repo 루트 기준 절대 경로.
    segments = clean.split("/");
  } else {
    // 현재 파일이 있는 디렉터리 기준 상대 경로.
    const baseDir = baseFilePath ? baseFilePath.split("/").slice(0, -1) : [];
    segments = [...baseDir, ...clean.split("/")];
  }

  const stack: string[] = [];
  for (const seg of segments) {
    if (seg === "" || seg === ".") continue;
    if (seg === "..") {
      if (stack.length === 0) return null; // repo 루트 위로 벗어남.
      stack.pop();
    } else {
      stack.push(seg);
    }
  }
  if (stack.length === 0) return null;
  return stack.join("/");
}

// 본문 링크 href를 분류한다.
// baseFilePath: 현재 뷰어가 보고 있는 파일 경로(상대 링크 기준점).
export function classifyLink(href: string, baseFilePath: string | undefined): ResolvedLink {
  const trimmed = href.trim();
  if (!trimmed) return { type: "ignore" };

  // 페이지 내 앵커.
  if (trimmed.startsWith("#")) return { type: "anchor", hash: trimmed };

  // 절대 http(s) URL → 외부 새 탭(앱 네비게이션은 막음).
  if (isAbsoluteHttp(trimmed)) return { type: "external", href: trimmed };

  // mailto/tel 등 다른 스킴은 무시(외부 이동/네비게이션 금지).
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed)) return { type: "ignore" };

  // 상대/루트 경로 → repo 파일로 해석.
  const path = resolveRepoPath(baseFilePath, trimmed);
  if (!path) return { type: "ignore" };
  return { type: "repo-file", path };
}
