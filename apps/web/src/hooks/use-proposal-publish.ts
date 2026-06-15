"use client";

import { useState } from "react";

import { generateProposals, type Proposal, publishProposal } from "../lib/api";

type PublishResult = { ok: boolean; text: string };

// 생성/발행 책임을 컴포넌트에서 분리한다.
// 멱등성: 같은 저장소에 대해 생성된 제안을 캐시해, 재발행 시 다시 생성하지 않는다.
export function useProposalPublish() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PublishResult | null>(null);
  const [cached, setCached] = useState<{ repo: string; proposal: Proposal } | null>(null);

  const reset = () => {
    setResult(null);
    setCached(null);
  };

  const publish = async (repo: string, issueNumber: number) => {
    const key = repo.trim();
    setBusy(true);
    setResult(null);
    try {
      let proposal = cached && cached.repo === key ? cached.proposal : null;
      if (!proposal) {
        const [generated] = await generateProposals(key);
        if (!generated) throw new Error("생성된 제안이 없습니다");
        proposal = generated;
        setCached({ repo: key, proposal });
      }
      const url = await publishProposal(proposal.id, issueNumber);
      setResult({ ok: true, text: url });
    } catch (cause) {
      setResult({ ok: false, text: cause instanceof Error ? cause.message : "알 수 없는 오류" });
    } finally {
      setBusy(false);
    }
  };

  return { busy, result, publish, reset };
}
