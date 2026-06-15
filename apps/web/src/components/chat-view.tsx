"use client";

import { useState } from "react";

import { DEMO_RESPONSE, SOURCES, SUGGESTIONS } from "../lib/fixtures";
import { selectScopeCount, useWorkspace } from "../lib/store";
import { AgentMessage } from "./agent-message";
import { Icon } from "./icon";
import { ProposalCard } from "./proposal-card";

export function ChatView() {
  const scopeCount = useWorkspace(selectScopeCount);
  const activeThreadId = useWorkspace((s) => s.activeThreadId);
  const [query, setQuery] = useState("");
  const canSend = query.trim().length > 0;

  return (
    <>
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-5 py-6">
          <div className="rounded-2xl border border-border bg-secondary/40 p-4">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary">
                <Icon name="hub" size={20} />
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-[15px] font-semibold">
                  {activeThreadId ?? "team 워크스페이스"}
                </h1>
                <p className="text-[11px] text-muted-foreground">
                  {activeThreadId ? "이어지는 대화" : `소스 ${SOURCES.length}개 · 모든 브랜치 인덱싱`}
                </p>
              </div>
              <span className="ml-auto inline-flex shrink-0 items-center gap-1 rounded-full bg-primary/10 px-2 py-1 text-[11px] font-medium text-primary">
                <Icon name="check_circle" size={12} />
                {scopeCount}개 소스 기준
              </span>
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
              연결된 저장소·문서를 근거로 질문에 답하고, 코드와 문서가 어긋난 부분을 찾아
              제안합니다. 답변에는 항상 출처(파일·라인·커밋)가 따라옵니다.
            </p>
          </div>

          {/* 추천 질문: 클릭 시 입력창을 채운다 */}
          <div className="mt-4 space-y-1.5">
            {SUGGESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuery(q)}
                className="flex w-full items-center gap-2.5 rounded-xl border border-border px-3 py-2 text-left text-[13px] text-foreground transition-colors hover:bg-secondary"
              >
                <Icon name="add_circle" size={16} className="text-muted-foreground" />
                <span className="flex-1">{q}</span>
              </button>
            ))}
          </div>

          {/* 예시 대화는 진행 중인 스레드에서만 표시. 실제 연동 시 DEMO_RESPONSE를
              백엔드 답변 그래프 출력(AgentResponse)으로 대체한다. */}
          {activeThreadId ? (
            <div className="mt-6 space-y-3">
              <AgentMessage response={DEMO_RESPONSE} />
              <ProposalCard />
            </div>
          ) : null}
        </div>
      </div>

      <div className="shrink-0 px-4 pb-4">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-border bg-background px-3.5 py-2.5 shadow-sm">
          <textarea
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="무엇이든 물어보세요"
            aria-label="메시지 입력"
            className="max-h-28 flex-1 resize-none bg-transparent text-[13px] leading-relaxed outline-none placeholder:text-muted-foreground"
          />
          <button
            type="button"
            disabled={!canSend}
            aria-label="보내기"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            <Icon name="arrow_upward" size={18} />
          </button>
        </div>
        <p className="mx-auto mt-1.5 max-w-2xl text-center text-[11px] text-muted-foreground">
          RepoLM의 답변은 부정확할 수 있으니 출처를 확인하세요.
        </p>
      </div>
    </>
  );
}
