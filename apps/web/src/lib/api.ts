// 백엔드 API 타입 클라이언트. 세션 쿠키를 쓰므로 모든 요청에 credentials:"include".
import type {
  Notebook,
  NotebookChatMessageList,
  NotebookChatResponse,
  NotebookDetail,
  Source,
  SourceCreate,
  SourceDetail,
  TreeNode,
} from "./types";

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
  signal?: AbortSignal,
): Promise<NotebookChatResponse> {
  return request(`/notebooks/${nid}/chat`, {
    method: "POST",
    body: JSON.stringify({ question, source_ids: sourceIds }),
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

export interface RepoRagSyncJobView {
  id: string;
  repository_id: string | null;
  trigger_type: string;
  branch: string;
  requested_commit_sha: string | null;
  idempotency_key: string;
  status: string;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface RepoRagSyncEvent {
  id: string;
  job_id: string;
  stage: string;
  detail: string;
  created_at: string;
}

export interface RepoRagSyncResponse {
  job: RepoRagSyncJobView;
  events: RepoRagSyncEvent[];
}

export interface RepoRagSyncRunResponse {
  status: number;
  response: RepoRagSyncResponse;
}

export interface RepoRagSyncRequest {
  repository: string;
  branch: string;
  repository_url: string;
}

export async function runRepoRagSync(
  body: RepoRagSyncRequest,
): Promise<RepoRagSyncRunResponse> {
  const res = await fetch(`${API_BASE}/pipeline/sync`, {
    credentials: "include",
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status})`);
  }

  return {
    status: res.status,
    response: (await res.json()) as RepoRagSyncResponse,
  };
}

export async function getRepoRagSyncJob(jobId: string): Promise<RepoRagSyncResponse> {
  return request(`/pipeline/sync/${jobId}`);
}
