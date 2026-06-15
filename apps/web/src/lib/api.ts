// 백엔드 API 타입 클라이언트. 세션 쿠키를 쓰므로 모든 요청에 credentials:"include".
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Me {
  user_id: number;
  login: string;
}

export interface Proposal {
  id: string;
  repository: string;
  target_path: string;
  proposed_change: string;
  confidence: number;
  status: string;
}

export function loginUrl(): string {
  return `${API_BASE}/auth/github/login`;
}

export async function getMe(): Promise<Me | null> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    credentials: "include",
    cache: "no-store",
  });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`사용자 조회 실패 (${res.status})`);
  return (await res.json()) as Me;
}

// 샘플 파일로 제안을 생성한다(in-memory 저장). repository를 지정하면 발행 대상 저장소가 된다.
export async function generateProposals(repository: string): Promise<Proposal[]> {
  const res = await fetch(`${API_BASE}/pipeline/proposals`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repository,
      files: [
        {
          path: "docs/auth.md",
          content: "# 인증\n토큰 만료(401) 처리를 문서에 추가하세요.\n",
        },
      ],
    }),
  });
  if (!res.ok) throw new Error(`제안 생성 실패 (${res.status})`);
  return ((await res.json()) as { proposals: Proposal[] }).proposals;
}

export async function publishProposal(id: string, issueNumber: number): Promise<string> {
  const res = await fetch(
    `${API_BASE}/github/proposals/${encodeURIComponent(id)}/publish`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue_number: issueNumber }),
    }
  );
  if (res.status === 401 || res.status === 403) {
    throw new Error("GitHub 로그인이 필요합니다");
  }
  if (!res.ok) {
    throw new Error(`발행 실패 (${res.status})`);
  }
  return ((await res.json()) as { comment_url: string }).comment_url;
}
