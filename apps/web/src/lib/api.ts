// 백엔드 API 타입 클라이언트. 세션 쿠키를 쓰므로 모든 요청에 credentials:"include".
import type {
  IndexProgress,
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

// 공통 JSON fetch 헬퍼. 세션 쿠키 포함, 실패 시 throw.
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    cache: "no-store",
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) throw new Error(`요청 실패 (${res.status})`);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ── 인증(기존 유지) ────────────────────────────────────────────────
export function loginUrl(): string {
  return `${API_BASE}/auth/github/login`;
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

export function createNotebook(body: { title: string; summary?: string }): Promise<Notebook> {
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

export function updateNotebook(
  nid: string,
  body: { title?: string; summary?: string },
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

// ── GitHub 공개 API(브랜치 자동 인식) ─────────────────────────────
// 비인증 fetch. 입력 URL이 github.com/{owner}/{repo} 형태일 때만 호출한다.
// 실패/비공개/레이트리밋이면 null을 반환해 호출부가 수동 입력으로 폴백하게 한다.

export interface GitHubRepoInfo {
  owner: string;
  repo: string;
  defaultBranch: string;
  branches: string[];
}

// 입력 문자열에서 owner/repo를 파싱. github.com 호스트가 아니면 null.
export function parseGitHubRepo(input: string): { owner: string; repo: string } | null {
  const url = input.trim();
  if (!url) return null;
  // https://github.com/owner/repo(.git)(/...) · github.com/owner/repo · git@github.com:owner/repo
  const m = url.match(
    /(?:^|\/\/|@)github\.com[/:]([^/\s]+)\/([^/\s#?]+?)(?:\.git)?(?:[/#?].*)?$/i,
  );
  if (!m) return null;
  const owner = m[1];
  const repo = m[2];
  if (!owner || !repo) return null;
  return { owner, repo };
}

// 공개 저장소의 default_branch + 브랜치 목록을 인식.
// signal로 디바운스 중 취소 가능. 실패 시 throw(호출부에서 폴백 처리).
export async function fetchGitHubRepoInfo(
  owner: string,
  repo: string,
  signal?: AbortSignal,
): Promise<GitHubRepoInfo> {
  const base = `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`;
  const headers = { Accept: "application/vnd.github+json" };
  // 1) default_branch
  const repoRes = await fetch(base, { headers, signal });
  if (!repoRes.ok) throw new Error(`GitHub 조회 실패 (${repoRes.status})`);
  const repoJson = (await repoRes.json()) as { default_branch?: string };
  const defaultBranch = repoJson.default_branch || "main";
  // 2) 브랜치 목록(최대 100개)
  const brRes = await fetch(`${base}/branches?per_page=100`, { headers, signal });
  if (!brRes.ok) throw new Error(`브랜치 조회 실패 (${brRes.status})`);
  const brJson = (await brRes.json()) as Array<{ name: string }>;
  const names = brJson.map((b) => b.name);
  // default_branch가 목록에 없으면 맨 앞에 보강.
  const branches = names.includes(defaultBranch) ? names : [defaultBranch, ...names];
  return { owner, repo, defaultBranch, branches };
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
