"use client";

import { useState } from "react";

import { useProposalPublish } from "../hooks/use-proposal-publish";
import { SOURCES, TODAY } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";

const PROPOSAL_TITLE = "문서 반영: docs/auth.md 401 처리";
const isoToday = `${TODAY.getFullYear()}-${String(TODAY.getMonth() + 1).padStart(2, "0")}-${String(
  TODAY.getDate(),
).padStart(2, "0")}`;

export function ProposalCard() {
  const selected = useWorkspace((s) => s.selected);
  const addBoardTask = useWorkspace((s) => s.addBoardTask);
  const setCenterTab = useWorkspace((s) => s.setCenterTab);

  // 발행 대상 repo는 "범위에 포함된 첫 저장소"로 자동 채운다.
  const defaultRepo =
    SOURCES.find((s) => s.kind === "repo" && selected[s.id])?.name ?? "team/api";

  const [decision, setDecision] = useState<"none" | "approved" | "rejected">("none");
  const [addedToBoard, setAddedToBoard] = useState(false);
  const [repo, setRepo] = useState(defaultRepo);
  const [issue, setIssue] = useState("");
  const { busy, result, publish } = useProposalPublish();

  const canPublish = repo.trim().includes("/") && /^\d+$/.test(issue.trim()) && !busy;

  const approve = () => {
    setDecision("approved");
    addBoardTask({ title: PROPOSAL_TITLE, status: "todo", due: isoToday, repo: defaultRepo });
    setAddedToBoard(true);
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
        <Icon name="auto_awesome" size={16} className="text-primary" />
        제안 · 관련 코드
        <span className="ml-auto">confidence 0.86</span>
      </div>
      <p className="mt-2 text-[14px] leading-relaxed">
        <code className="rounded bg-secondary px-1 py-0.5 text-[13px]">docs/auth.md</code> 가 토큰
        만료 케이스를 다루지 않습니다. 인증 미들웨어의 401 처리를 문서에 반영하길 제안합니다.
      </p>

      {decision === "none" ? (
        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={approve}
            className="rounded-lg bg-primary px-3.5 py-1.5 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            승인
          </button>
          <button
            type="button"
            onClick={() => setDecision("rejected")}
            className="rounded-lg border border-border px-3.5 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            반려
          </button>
        </div>
      ) : decision === "rejected" ? (
        <p className="mt-3 text-[13px] text-muted-foreground">반려됨</p>
      ) : (
        <div className="mt-3 space-y-3">
          {addedToBoard ? (
            <div className="flex items-center gap-2 rounded-lg bg-primary/10 px-2.5 py-1.5 text-[12px] text-primary">
              <Icon name="check_circle" size={14} />
              보드 &ldquo;할 일&rdquo;에 추가됨
              <button
                type="button"
                onClick={() => setCenterTab("보드")}
                className="ml-auto inline-flex items-center gap-0.5 font-medium underline"
              >
                보드에서 보기
              </button>
            </div>
          ) : null}

          <div>
            <p className="mb-1.5 text-[12px] text-muted-foreground">
              GitHub 기존 이슈에 코멘트로 발행
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="owner/repo"
                aria-label="발행 대상 저장소"
                className="w-40 rounded-md border border-input bg-secondary px-2 py-1 text-[12px] outline-none placeholder:text-muted-foreground"
              />
              <input
                value={issue}
                onChange={(e) => setIssue(e.target.value)}
                placeholder="이슈 #"
                inputMode="numeric"
                aria-label="이슈 번호"
                className="w-20 rounded-md border border-input bg-secondary px-2 py-1 text-[12px] outline-none placeholder:text-muted-foreground"
              />
              <button
                type="button"
                onClick={() => publish(repo.trim(), Number(issue.trim()))}
                disabled={!canPublish}
                className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-[12px] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                <Icon name="north_east" size={14} />
                {busy ? "발행 중…" : "GitHub에 발행"}
              </button>
            </div>
          </div>

          {result ? (
            result.ok ? (
              <a
                href={result.text}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[12px] text-primary underline"
              >
                <Icon name="check_circle" size={14} /> 발행됨 — 코멘트 열기
              </a>
            ) : (
              <p className="inline-flex items-center gap-1 text-[12px] text-destructive">
                <Icon name="north_east" size={14} /> {result.text}
              </p>
            )
          ) : null}
        </div>
      )}
    </div>
  );
}
