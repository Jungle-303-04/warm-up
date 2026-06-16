"use client";

import { useState } from "react";

import { CHAT_SUMMARY, DEMO_RESPONSE, SUGGESTIONS } from "../lib/fixtures";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type { AgentResponse } from "../lib/types";
import { AgentMessage } from "./agent-message";
import { ChatEmpty } from "./chat-empty";
import { Icon } from "./icon";

interface Turn {
  question: string;
  response: AgentResponse;
}

export function ChatView() {
  const scopeCount = useWorkspace(selectScopeCount);
  const sourceCount = useWorkspace((s) => s.sources.length);
  const [query, setQuery] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const canSend = query.trim().length > 0;

  // 오늘 날짜(목업 메타). 클라이언트 로캘로 표시.
  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // 목업: 입력을 보내면 데모 답변을 덧붙인다(실제 연동 시 백엔드 답변 그래프로 대체).
  const send = () => {
    if (!canSend) return;
    setTurns((prev) => [...prev, { question: query.trim(), response: DEMO_RESPONSE }]);
    setQuery("");
  };

  // 소스 0개: 빈 채팅 대신 온보딩 히어로를 보여준다.
  if (sourceCount === 0) return <ChatEmpty />;

  return (
    <>
      <div className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-6 py-6">
          {/* 환영 카드 */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-elev-1">
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-accent text-accent-foreground shadow-elev-1">
                <Icon name="hub" size={22} />
              </span>
              <div className="min-w-0 flex-1">
                <h1 className="truncate text-[16px] font-semibold tracking-tight">RepoLM 대화</h1>
                <p className="mt-0.5 truncate text-[11.5px] text-muted-foreground">
                  소스 {sourceCount}개 연결됨 · {today}
                </p>
              </div>
              <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-accent px-2.5 py-1 text-[11px] font-semibold text-accent-foreground">
                <Icon name="check_circle" size={13} />
                {scopeCount}개 기준
              </span>
            </div>
            <p className="mt-3.5 text-[13.5px] leading-relaxed text-muted-foreground">
              연결된 저장소·문서를 근거로 질문에 답하고, 코드와 문서가 어긋난 부분을 찾습니다.
              답변에는 항상 출처(파일·라인·커밋)가 따라옵니다.
            </p>
          </div>

          {/* 요약 카드: 생성된 듯한 개요 + 하단 액션 줄(메모 저장/복사/좋아요/싫어요) */}
          <div className="mt-4 rounded-2xl border border-border bg-card p-5 shadow-elev-1">
            <div className="flex items-center gap-2 text-[12px] font-medium text-muted-foreground">
              <Icon name="auto_awesome" size={14} className="text-primary" />
              요약
            </div>
            <p className="mt-2.5 text-[14px] leading-relaxed text-foreground">
              {CHAT_SUMMARY.map((s, i) =>
                s.bold ? (
                  <strong key={i} className="font-semibold">
                    {s.seg}
                  </strong>
                ) : (
                  <span key={i}>{s.seg}</span>
                ),
              )}
            </p>
            {/* 액션 줄: 아이콘 버튼(목업) */}
            <div className="mt-3.5 flex items-center gap-1 border-t border-border pt-3">
              <button
                type="button"
                className="interactive inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-[12px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="save_note" size={15} /> 메모에 저장
              </button>
              <span className="flex-1" />
              <button
                type="button"
                aria-label="복사"
                title="복사"
                className="interactive grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="copy" size={15} />
              </button>
              <button
                type="button"
                aria-label="좋아요"
                title="좋아요"
                className="interactive grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="thumb_up" size={15} />
              </button>
              <button
                type="button"
                aria-label="싫어요"
                title="싫어요"
                className="interactive grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="thumb_down" size={15} />
              </button>
            </div>
          </div>

          {/* 추천 질문: 둥근 카드 칩. 클릭 시 입력창을 채운다 */}
          {turns.length === 0 ? (
            <div className="mt-5">
              <p className="mb-2.5 flex items-center gap-1.5 px-1 text-[12px] font-medium text-muted-foreground">
                <Icon name="lightbulb" size={14} className="text-primary" />
                추천 질문
              </p>
              <div className="space-y-2">
                {SUGGESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuery(q)}
                    className="interactive group flex w-full items-center gap-3 rounded-2xl border border-border bg-card px-4 py-3 text-left text-[13.5px] text-foreground hover:border-primary/40 hover:bg-secondary hover:shadow-elev-1"
                  >
                    <span className="flex-1 leading-snug">{q}</span>
                    <Icon
                      name="north_east"
                      size={15}
                      className="shrink-0 text-muted-foreground/60 transition-colors group-hover:text-primary"
                    />
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* 대화 턴(목업) */}
          <div className="mt-7 space-y-6">
            {turns.map((turn, i) => (
              <div key={i} className="space-y-3.5">
                <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-[13.5px] leading-relaxed text-primary-foreground shadow-elev-1">
                  {turn.question}
                </div>
                <div className="flex gap-2.5">
                  <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
                    <Icon name="hub" size={16} />
                  </span>
                  <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md border border-border bg-card px-4 py-3 shadow-elev-1">
                    <AgentMessage response={turn.response} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 하단 입력바 */}
      <div className="shrink-0 px-5 pb-5">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-[26px] border border-border bg-card px-3 py-2.5 shadow-elev-2 focus-within:border-primary/50">
          <button
            type="button"
            aria-label="첨부"
            title="첨부"
            className="interactive mb-0.5 grid h-9 w-9 shrink-0 place-items-center self-end rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <Icon name="attach" size={18} />
          </button>
          <textarea
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="무엇이든 물어보세요"
            aria-label="메시지 입력"
            className="max-h-32 flex-1 resize-none self-center bg-transparent py-1.5 text-[14px] leading-relaxed outline-none placeholder:text-muted-foreground"
          />
          <div className="flex shrink-0 items-center gap-2 self-end pb-0.5">
            <span className="hidden items-center gap-1 text-[11px] text-muted-foreground sm:inline-flex">
              <Icon name="description" size={12} />
              소스 {sourceCount}개
            </span>
            <button
              type="button"
              onClick={send}
              disabled={!canSend}
              aria-label="보내기"
              className="interactive grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:active:scale-100"
            >
              <Icon name="arrow_upward" size={18} />
            </button>
          </div>
        </div>
        <p className="mx-auto mt-2 max-w-2xl text-center text-[11px] text-muted-foreground">
          RepoLM의 답변은 부정확할 수 있으니 출처를 확인하세요.
        </p>
      </div>
    </>
  );
}
