export type ProposalStatus = "pending" | "approved" | "rejected";

export interface Proposal {
  id: string;
  repository: string;
  target_path: string;
  type: string;
  proposed_change: string;
  evidence: string[];
  confidence: number;
  status: ProposalStatus;
  created_at: string;
  decided_at: string | null;
  decided_reason: string | null;
}

interface ProposalListResponse {
  proposals: Proposal[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function listProposals(status?: ProposalStatus): Promise<Proposal[]> {
  const url = new URL(`${API_BASE}/pipeline/proposals`);
  if (status) {
    url.searchParams.set("status", status);
  }

  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`제안 목록 조회 실패 (${response.status})`);
  }

  const data = (await response.json()) as ProposalListResponse;
  return data.proposals;
}

export async function decideProposal(
  id: string,
  action: "approve" | "reject",
  reason?: string
): Promise<Proposal> {
  const response = await fetch(`${API_BASE}/pipeline/proposals/${id}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason ?? null })
  });

  if (!response.ok) {
    throw new Error(`${action === "approve" ? "승인" : "반려"} 실패 (${response.status})`);
  }

  return (await response.json()) as Proposal;
}
