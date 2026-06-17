// 백엔드 API 타입 클라이언트. 세션 쿠키를 쓰므로 모든 요청에 credentials:"include".
import type {
  Artifact,
  ArtifactType,
  GeneratableArtifactType,
  IndexProgress,
  LinkMetadata,
  Notebook,
  NotebookChatMessageList,
  NotebookChatResponse,
  NotebookDetail,
  Source,
  SourceCreate,
  SourceDetail,
  TreeNode,
} from "./types";

export { API_BASE };

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Me {
  user_id: number;
  login: string;
}

// HTTP 상태 코드를 보존하는 API 에러. 호출부가 401(로그인 필요) 등을 분기할 수 있게 한다.
export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message?: string) {
    super(message ?? `요청 실패 (${status})`);
    this.name = "ApiError";
    this.status = status;
  }
}

// 에러가 특정 HTTP 상태인지 판정하는 헬퍼.
export function isApiStatus(error: unknown, status: number): boolean {
  return error instanceof ApiError && error.status === status;
}

// 인증 실패(401)인지 판정. 로그인 안내 분기에 사용.
export function isUnauthorized(error: unknown): boolean {
  return isApiStatus(error, 401);
}

// 공통 JSON fetch 헬퍼. 세션 쿠키 포함, 실패 시 status 보존한 ApiError throw.
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    cache: "no-store",
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) {
    let message = `요청 실패 (${res.status})`;
    try {
      const payload = (await res.json()) as { detail?: unknown };
      if (typeof payload.detail === "string" && payload.detail.trim()) {
        message = payload.detail;
      }
    } catch {
      // JSON 에러 본문이 아니면 기본 status 메시지를 유지한다.
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ── 인증(기존 유지) ────────────────────────────────────────────────
export function loginUrl(): string {
  return `${API_BASE}/auth/github/login`;
}

// 로그아웃. rp_session 쿠키를 서버에서 만료시킨다(204). 쿠키만 지우므로 인증 불필요.
export function logout(): Promise<void> {
  return request("/auth/logout", { method: "POST" });
}

export async function getMe(signal?: AbortSignal): Promise<Me | null> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    credentials: "include",
    cache: "no-store",
    signal,
  });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`사용자 조회 실패 (${res.status})`);
  return (await res.json()) as Me;
}

// ── 노트북 CRUD ───────────────────────────────────────────────────
export function listNotebooks(): Promise<{ notebooks: Notebook[] }> {
  return request("/notebooks");
}

export function createNotebook(body: { title?: string }): Promise<Notebook> {
  return request("/notebooks", { method: "POST", body: JSON.stringify(body) });
}

export function getNotebook(nid: string): Promise<NotebookDetail> {
  return request(`/notebooks/${nid}`);
}

export function askNotebook(
  nid: string,
  question: string,
  sourceIds: string[] | null,
  filePaths: string[] | null,
  signal?: AbortSignal,
): Promise<NotebookChatResponse> {
  return request(`/notebooks/${nid}/chat`, {
    method: "POST",
    body: JSON.stringify({ question, source_ids: sourceIds, file_paths: filePaths }),
    signal,
  });
}

export function listNotebookChatMessages(nid: string): Promise<NotebookChatMessageList> {
  return request(`/notebooks/${nid}/chat/messages`);
}

export function clearNotebookChatMessages(nid: string): Promise<void> {
  return request(`/notebooks/${nid}/chat/messages`, { method: "DELETE" });
}

export function updateNotebook(
  nid: string,
  body: { title?: string },
): Promise<Notebook> {
  return request(`/notebooks/${nid}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function deleteNotebook(nid: string): Promise<void> {
  return request(`/notebooks/${nid}`, { method: "DELETE" });
}

// ── 소스 ──────────────────────────────────────────────────────────
export function listSources(nid: string): Promise<{ sources: Source[] }> {
  return request(`/notebooks/${nid}/sources`);
}

export function createSource(nid: string, body: SourceCreate): Promise<Source> {
  return request(`/notebooks/${nid}/sources`, { method: "POST", body: JSON.stringify(body) });
}

export function getSource(nid: string, sid: string): Promise<SourceDetail> {
  return request(`/notebooks/${nid}/sources/${sid}`);
}

export function deleteSource(nid: string, sid: string): Promise<void> {
  return request(`/notebooks/${nid}/sources/${sid}`, { method: "DELETE" });
}

// ── 산출물(아티팩트/메모) ─────────────────────────────────────────
// 다이어그램/요약 산출물 생성. source_ids 미지정 시 백엔드가 노트북 전체 소스를 사용.
export function createArtifact(
  nid: string,
  body: { type: GeneratableArtifactType; source_ids?: string[] },
): Promise<Artifact> {
  return request(`/notebooks/${nid}/artifacts`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// 메모(type:"note") 생성. content 는 빈 문자열도 허용.
export function createNote(
  nid: string,
  body: { title?: string; content: string },
): Promise<Artifact> {
  return request(`/notebooks/${nid}/artifacts/note`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listArtifacts(nid: string): Promise<{ artifacts: Artifact[] }> {
  return request(`/notebooks/${nid}/artifacts`);
}

export function getArtifact(nid: string, aid: string): Promise<Artifact> {
  return request(`/notebooks/${nid}/artifacts/${aid}`);
}

export function updateArtifact(
  nid: string,
  aid: string,
  body: { title?: string; content?: string },
): Promise<Artifact> {
  return request(`/notebooks/${nid}/artifacts/${aid}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteArtifact(nid: string, aid: string): Promise<void> {
  return request(`/notebooks/${nid}/artifacts/${aid}`, { method: "DELETE" });
}

// 산출물 타입 별 표시 메타(레이블/아이콘/색조)의 단일 소스. UI 전역에서 재사용.
export const ARTIFACT_META: Record<
  ArtifactType,
  { label: string; icon: string; tint: string }
> = {
  uml: { label: "UML", icon: "account_tree", tint: "blue" },
  erd: { label: "ERD", icon: "schema", tint: "violet" },
  dependency: { label: "의존성 그래프", icon: "hub", tint: "teal" },
  change_summary: { label: "변경 요약", icon: "difference", tint: "amber" },
  note: { label: "메모", icon: "sticky_note_2", tint: "grey" },
};

// 산출물이 Mermaid 다이어그램인지(렌더 분기용).
export function isMermaidArtifact(type: ArtifactType): boolean {
  return type === "uml" || type === "erd" || type === "dependency";
}

// ── repo 소스: 파일 트리 / 단일 파일 ───────────────────────────────
export function getTree(nid: string, sid: string): Promise<{ tree: TreeNode[] }> {
  return request(`/notebooks/${nid}/sources/${sid}/tree`);
}

export function getFile(
  nid: string,
  sid: string,
  path: string,
): Promise<{ path: string; content: string }> {
  return request(`/notebooks/${nid}/sources/${sid}/file?path=${encodeURIComponent(path)}`);
}

// ── RAG 인덱싱 진행 ───────────────────────────────────────────────
// 1회 조회(재접속/초기 상태 복원용).
export function getIndexProgress(nid: string, sid: string): Promise<IndexProgress> {
  return request(`/notebooks/${nid}/sources/${sid}/index`);
}

// 인덱싱 재실행(정지/실패 회복용). repo면 재클론→재인덱싱.
// 즉시 status:"queued"인 IndexProgress를 반환한다.
export function reindexSource(nid: string, sid: string): Promise<IndexProgress> {
  return request(`/notebooks/${nid}/sources/${sid}/reindex`, { method: "POST" });
}

// ── 링크 메타데이터(URL 소스 제목/아이콘 자동 채움) ─────────────────
// GET /link-metadata?url=<URL> (쿠키 인증). 실패해도 200(가능 필드만, icon_url은 s2 폴백).
// signal로 디바운스 중 취소 가능. 네트워크 오류 시 throw(호출부에서 폴백 처리).
export function getLinkMetadata(url: string, signal?: AbortSignal): Promise<LinkMetadata> {
  return request(`/link-metadata?url=${encodeURIComponent(url)}`, { signal });
}

// ── GitHub 공개 API(브랜치 자동 인식) ─────────────────────────────
// 비인증 fetch. 입력 URL이 github.com/{owner}/{repo} 형태일 때만 호출한다.
// 실패/비공개/레이트리밋이면 null을 반환해 호출부가 수동 입력으로 폴백하게 한다.

export interface GitHubRepoInfo {
  owner: string;
  repo: string;
  defaultBranch: string;
  branches: string[];
}

export interface ParsedGitHubRepo {
  owner: string;
  repo: string;
  repositoryUrl: string;
  branch?: string;
}

function stripGitSuffix(value: string): string {
  return value.replace(/\.git$/i, "");
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

// 입력 문자열에서 owner/repo와 선택적으로 /tree|blob/{branch}를 파싱한다.
// 브랜치가 URL에 같이 들어와도 백엔드에는 항상 정규화된 repo URL만 보낸다.
export function parseGitHubRepo(input: string): ParsedGitHubRepo | null {
  const raw = input.trim();
  if (!raw) return null;

  const ssh = raw.match(/^git@github\.com:([^/\s]+)\/([^\s#?]+?)(?:\.git)?$/i);
  if (ssh) {
    const owner = ssh[1];
    const repo = stripGitSuffix(ssh[2]);
    return {
      owner,
      repo,
      repositoryUrl: `https://github.com/${owner}/${repo}`,
    };
  }

  let parsed: URL;
  try {
    parsed = new URL(raw.includes("://") ? raw : `https://${raw}`);
  } catch {
    return null;
  }

  if (parsed.hostname.toLowerCase() !== "github.com") return null;
  const parts = parsed.pathname.split("/").filter(Boolean).map(safeDecode);
  if (parts.length < 2) return null;

  const owner = parts[0];
  const repo = stripGitSuffix(parts[1]);
  if (!owner || !repo) return null;

  const branch =
    (parts[2] === "tree" || parts[2] === "blob") && parts.length > 3
      ? parts.slice(3).join("/")
      : undefined;

  return {
    owner,
    repo,
    repositoryUrl: `https://github.com/${owner}/${repo}`,
    branch,
  };
}

export function resolveGitHubBranchFromPath(
  branchPath: string | undefined,
  branches: string[],
): string | null {
  if (!branchPath) return null;
  if (branches.includes(branchPath)) return branchPath;
  const candidates = branches
    .filter((branch) => branchPath === branch || branchPath.startsWith(`${branch}/`))
    .sort((a, b) => b.length - a.length);
  return candidates[0] ?? null;
}

// 공개 저장소의 default_branch + 브랜치 목록을 인식.
// signal로 디바운스 중 취소 가능. 실패 시 throw(호출부에서 폴백 처리).
export async function fetchGitHubRepoInfo(
  owner: string,
  repo: string,
  signal?: AbortSignal,
): Promise<GitHubRepoInfo> {
  return request(
    `/github/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/info`,
    { signal },
  );
}

// SSE 구독. 반환값 close()로 반드시 정리(EventSource 누수 방지).
// onProgress: data 이벤트마다 호출, onDone: status done/failed로 종료 시 1회 호출.
export function openIndexStream(
  nid: string,
  sid: string,
  onProgress: (progress: IndexProgress) => void,
  onDone?: (progress: IndexProgress | null) => void,
): { close: () => void } {
  const es = new EventSource(`${API_BASE}/notebooks/${nid}/sources/${sid}/index/stream`, {
    withCredentials: true,
  });
  let last: IndexProgress | null = null;
  let closed = false;

  const close = () => {
    if (closed) return;
    closed = true;
    es.close();
  };

  es.onmessage = (event) => {
    let progress: IndexProgress;
    try {
      progress = JSON.parse(event.data) as IndexProgress;
    } catch {
      return; // 파싱 실패 프레임은 무시.
    }
    last = progress;
    onProgress(progress);
    if (progress.status === "done" || progress.status === "failed") {
      close();
      onDone?.(progress);
    }
  };

  // 네트워크 오류 등으로 끊기면 정리(브라우저 자동 재연결 대신 명시적 종료).
  es.onerror = () => {
    close();
    onDone?.(last);
  };

  return { close };
}
