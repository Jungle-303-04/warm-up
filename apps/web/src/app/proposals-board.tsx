"use client";

import { useCallback, useEffect, useState } from "react";

import {
  decideProposal,
  listProposals,
  type Proposal,
  type ProposalStatus
} from "../lib/api";

type Filter = ProposalStatus | "all";

const FILTERS: { label: string; value: Filter }[] = [
  { label: "대기", value: "pending" },
  { label: "승인", value: "approved" },
  { label: "반려", value: "rejected" },
  { label: "전체", value: "all" }
];

export default function ProposalsBoard() {
  const [filter, setFilter] = useState<Filter>("pending");
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProposals(await listProposals(filter === "all" ? undefined : filter));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "알 수 없는 오류");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void load();
  }, [load]);

  const decide = async (id: string, action: "approve" | "reject") => {
    setBusyId(id);
    setError(null);
    try {
      await decideProposal(id, action);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "알 수 없는 오류");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="board">
      <div className="board-head">
        <div className="filters">
          {FILTERS.map((item) => (
            <button
              key={item.value}
              type="button"
              className={filter === item.value ? "chip chip-active" : "chip"}
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button type="button" className="chip" onClick={() => void load()}>
          새로고침
        </button>
      </div>

      {error ? <p className="board-error">⚠ {error}</p> : null}
      {loading ? <p className="board-empty">불러오는 중…</p> : null}
      {!loading && proposals.length === 0 ? (
        <p className="board-empty">표시할 제안이 없습니다.</p>
      ) : null}

      <ul className="proposal-list">
        {proposals.map((proposal) => (
          <li key={proposal.id} className="proposal-card">
            <div className="proposal-top">
              <code>{proposal.target_path}</code>
              <span className={`badge badge-${proposal.status}`}>{proposal.status}</span>
            </div>
            <p className="proposal-change">{proposal.proposed_change}</p>
            <div className="proposal-meta">
              <span>{proposal.repository}</span>
              <span>신뢰도 {Math.round(proposal.confidence * 100)}%</span>
            </div>
            {proposal.status === "pending" ? (
              <div className="proposal-actions">
                <button
                  type="button"
                  className="btn btn-approve"
                  disabled={busyId === proposal.id}
                  onClick={() => void decide(proposal.id, "approve")}
                >
                  승인
                </button>
                <button
                  type="button"
                  className="btn btn-reject"
                  disabled={busyId === proposal.id}
                  onClick={() => void decide(proposal.id, "reject")}
                >
                  반려
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
