"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { askNotebook, listNotebookChatMessages } from "../lib/api";
import { SUGGESTIONS } from "../lib/fixtures";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type { AgentResponse, NotebookChatMessage, NotebookChatResponse } from "../lib/types";
import { AgentMessage } from "./agent-message";
import { ChatEmpty } from "./chat-empty";
import { Icon } from "./icon";

interface Turn {
  question: string;
  response: AgentResponse;
}

function toAgentResponse(response: NotebookChatResponse): AgentResponse {
  if (response.citations.length === 0) {
    return { kind: "abstain", reason: response.answer };
  }
  return {
    kind: "answer",
    text: response.answer,
    citations: response.citations.map((citation) => ({
      sourceId: citation.source_id,
      sourceName: citation.source_title,
      path: citation.path ?? undefined,
      snippet: citation.snippet,
    })),
  };
}

function historyToTurns(messages: NotebookChatMessage[]): Turn[] {
  const turns: Turn[] = [];
  let pendingQuestion: string | null = null;

  for (const message of messages) {
    if (message.role === "user") {
      pendingQuestion = message.content;
      continue;
    }

    const question = pendingQuestion ?? "이전 답변";
    turns.push({
      question,
      response: toAgentResponse({ answer: message.content, citations: message.citations }),
    });
    pendingQuestion = null;
  }

  if (pendingQuestion) {
    turns.push({
      question: pendingQuestion,
      response: { kind: "abstain", reason: "이 질문의 답변 기록을 찾지 못했습니다." },
    });
  }

  return turns;
}

function draftKey(notebookId: string) {
  return `repolm.chatDraft.${notebookId}`;
}

export function ChatView() {
  const scopeCount = useWorkspace(selectScopeCount);
  const sourceCount = useWorkspace((s) => s.sources.length);
  const notebookId = useWorkspace((s) => s.notebookId);
  const selectedSourceIds = useWorkspace((s) => s.selectedSourceIds);
  const addNote = useWorkspace((s) => s.addNote);
  const [query, setQuery] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [sending, setSending] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [queuedQuestions, setQueuedQuestions] = useState<string[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const selectedSourceIdList = useMemo(() => [...selectedSourceIds], [selectedSourceIds]);
  const allSourcesSelected = sourceCount > 0 && scopeCount === sourceCount;
  const canSend = query.trim().length > 0 && scopeCount > 0 && !!notebookId;
  const [savedSummary, setSavedSummary] = useState(false);

  // 클라이언트 로캘 기준의 세션 날짜.
  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  useEffect(() => {
    if (!notebookId) return;
    let active = true;
    setLoadingHistory(true);
    setHistoryError(null);
    listNotebookChatMessages(notebookId)
      .then((history) => {
        if (active) setTurns(historyToTurns(history.messages));
      })
      .catch((error) => {
        if (!active) return;
        setHistoryError(error instanceof Error ? error.message : "대화 기록을 불러오지 못했습니다");
      })
      .finally(() => {
        if (active) setLoadingHistory(false);
      });
    return () => {
      active = false;
    };
  }, [notebookId]);

  useEffect(() => {
    if (!notebookId) return;
    try {
      setQuery(localStorage.getItem(draftKey(notebookId)) ?? "");
    } catch {
      setQuery("");
    }
  }, [notebookId]);

  useEffect(() => {
    if (!notebookId) return;
    try {
      localStorage.setItem(draftKey(notebookId), query);
    } catch {
      // 캐시 저장 실패는 대화 기능을 막지 않는다.
    }
  }, [notebookId, query]);

  const runQuestion = useCallback(
    async (question: string) => {
      if (!question || scopeCount === 0 || !notebookId) return;

      const sourceIds = allSourcesSelected ? null : selectedSourceIdList;
      const controller = new AbortController();
      abortRef.current = controller;
      setPendingQuestion(question);
      setSending(true);
      try {
        const response = await askNotebook(notebookId, question, sourceIds, controller.signal);
        setTurns((prev) => [...prev, { question, response: toAgentResponse(response) }]);
      } catch (error) {
        const wasAborted = controller.signal.aborted;
        const message = error instanceof Error ? error.message : "답변 요청 실패";
        setTurns((prev) => [
          ...prev,
          {
            question,
            response: {
              kind: "abstain",
              reason: wasAborted
                ? "진행 중인 답변 생성을 중지했습니다."
                : `답변을 가져오지 못했습니다. ${message}`,
            },
          },
        ]);
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        setPendingQuestion(null);
        setSending(false);
      }
    },
    [allSourcesSelected, notebookId, scopeCount, selectedSourceIdList],
  );

  useEffect(() => {
    if (sending || queuedQuestions.length === 0) return;
    const [next, ...rest] = queuedQuestions;
    setQueuedQuestions(rest);
    void runQuestion(next);
  }, [queuedQuestions, runQuestion, sending]);

  const send = async (text = query) => {
    const question = text.trim();
    if (!question || scopeCount === 0 || !notebookId) return;

    setQuery("");
    if (sending) {
      setQueuedQuestions((prev) => [...prev, question]);
      return;
    }
    await runQuestion(question);
  };

  const stopCurrent = () => {
    abortRef.current?.abort();
    setQueuedQuestions([]);
  };

  // 소스 0개: 빈 채팅 대신 온보딩 히어로를 보여준다.
  if (sourceCount === 0 && turns.length === 0 && !loadingHistory) return <ChatEmpty />;

  return (
    <>
      <div className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-6 py-5">
          <div className="rounded-2xl border border-border bg-card p-4 shadow-elev-1">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-2xl bg-accent text-accent-foreground shadow-elev-1">
                <Icon name="hub" size={19} />
              </span>
              <div className="min-w-0 flex-1">
                <h1 className="truncate text-[15px] font-semibold">RepoLM 대화</h1>
                <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                  소스 {sourceCount}개 연결됨 · {today}
                </p>
              </div>
              <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-accent px-2.5 py-1 text-[11px] font-semibold text-accent-foreground">
                <Icon name="check_circle" size={13} />
                {scopeCount}개 기준
              </span>
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
              연결된 저장소·문서를 근거로 질문에 답하고, 코드와 문서가 어긋난 부분을 찾습니다.
              답변에는 항상 출처(파일·라인·커밋)가 따라옵니다.
            </p>
          </div>

          {loadingHistory || historyError ? (
            <div className="mt-2.5 flex items-center gap-2 rounded-xl border border-border bg-surface-raised px-3 py-2 text-[11.5px] text-muted-foreground">
              <Icon
                name={loadingHistory ? "progress_activity" : "report"}
                size={13}
                className={loadingHistory ? "animate-spin" : "text-destructive"}
              />
              {loadingHistory ? "저장된 대화 기록을 불러오는 중" : historyError}
            </div>
          ) : null}

          <div className="mt-3 rounded-2xl border border-border bg-card p-4 shadow-elev-1">
            <div className="flex items-center gap-2 text-[11.5px] font-medium text-muted-foreground">
              <Icon name="auto_awesome" size={13} className="text-primary" />
              소스 상태
            </div>
            <p className="mt-2 text-[13px] leading-relaxed text-foreground">
              현재 <strong className="font-semibold">{sourceCount}개</strong> 소스 중{" "}
              <strong className="font-semibold">{scopeCount}개</strong>가 답변 범위에 포함되어
              있습니다. 질문을 보내면 백엔드가 선택된 소스에서 근거를 찾아 답변합니다.
            </p>
            <div className="mt-3 flex items-center gap-1 border-t border-border pt-2.5">
              <button
                type="button"
                onClick={() => {
                  addNote("대화 요약", `소스 ${scopeCount}개 · 방금 전`);
                  setSavedSummary(true);
                }}
                className="interactive inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name={savedSummary ? "check_circle" : "save_note"} size={14} />
                {savedSummary ? "저장됨" : "메모에 저장"}
              </button>
              <span className="flex-1" />
              <button
                type="button"
                aria-label="복사"
                title="복사"
                className="interactive grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="copy" size={14} />
              </button>
              <button
                type="button"
                aria-label="좋아요"
                title="좋아요"
                className="interactive grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="thumb_up" size={14} />
              </button>
              <button
                type="button"
                aria-label="싫어요"
                title="싫어요"
                className="interactive grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                <Icon name="thumb_down" size={14} />
              </button>
            </div>
          </div>

          {/* 추천 질문: 클릭 시 입력창을 채우고, 더블클릭 시 바로 전송한다. */}
          {turns.length === 0 ? (
            <div className="mt-4">
              <p className="mb-2 flex items-center gap-1.5 px-1 text-[11.5px] font-medium text-muted-foreground">
                <Icon name="lightbulb" size={13} className="text-primary" />
                추천 질문
              </p>
              <div className="space-y-1.5">
                {SUGGESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuery(q)}
                    onDoubleClick={() => void send(q)}
                    className="interactive group flex w-full items-center gap-3 rounded-xl border border-border bg-card px-3.5 py-2.5 text-left text-[13px] text-foreground hover:border-primary/40 hover:bg-secondary hover:shadow-elev-1"
                  >
                    <span className="flex-1 leading-snug">{q}</span>
                    <Icon
                      name="north_east"
                      size={14}
                      className="shrink-0 text-muted-foreground/60 transition-colors group-hover:text-primary"
                    />
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* 대화 턴 */}
          <div className="mt-6 space-y-5">
            {turns.map((turn, i) => (
              <div key={i} className="message-in space-y-3">
                <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-[13px] leading-relaxed text-primary-foreground shadow-elev-1">
                  {turn.question}
                </div>
                <div className="flex gap-2.5">
                  <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
                    <Icon name="hub" size={15} />
                  </span>
                  <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md border border-border bg-card px-3.5 py-2.5 shadow-elev-1">
                    <AgentMessage response={turn.response} />
                  </div>
                </div>
              </div>
            ))}
            {sending && pendingQuestion ? (
              <div className="message-in space-y-3">
                <div className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-[13px] leading-relaxed text-primary-foreground shadow-elev-1">
                  {pendingQuestion}
                </div>
                <div className="flex items-center gap-2.5 text-[12.5px] text-muted-foreground">
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
                    <Icon name="hub" size={15} />
                  </span>
                  <div className="rounded-2xl border border-border bg-card px-3 py-2 shadow-elev-1">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1" aria-hidden>
                        <span className="thinking-dot" />
                        <span className="thinking-dot" />
                        <span className="thinking-dot" />
                      </span>
                      <span>근거를 찾고 답변을 조립하는 중</span>
                      <button
                        type="button"
                        onClick={stopCurrent}
                        className="interactive ml-1 inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
                      >
                        <Icon name="stop_circle" size={13} />
                        중지
                      </button>
                    </div>
                    {queuedQuestions.length > 0 ? (
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        다음 질문 {queuedQuestions.length}개 대기 중
                      </p>
                    ) : null}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* 하단 입력바 */}
      <div className="shrink-0 px-5 pb-4">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-[24px] border border-border bg-card px-2.5 py-2 shadow-elev-2 focus-within:border-primary/50">
          <button
            type="button"
            aria-label="첨부"
            title="첨부"
            className="interactive mb-0.5 grid h-8 w-8 shrink-0 place-items-center self-end rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <Icon name="attach" size={17} />
          </button>
          <textarea
            rows={1}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            disabled={scopeCount === 0}
            placeholder={
              scopeCount === 0
                ? "왼쪽에서 소스를 선택하세요"
                : sending
                  ? "다음 질문을 입력하면 대기열에 추가됩니다"
                  : "무엇이든 물어보세요"
            }
            aria-label="메시지 입력"
            className="max-h-32 flex-1 resize-none self-center bg-transparent py-1.5 text-[13px] leading-relaxed outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed"
          />
          <div className="flex shrink-0 items-center gap-2 self-end pb-0.5">
            <span className="hidden items-center gap-1 text-[11px] text-muted-foreground sm:inline-flex">
              <Icon name="description" size={12} />
              소스 {scopeCount}/{sourceCount}개
            </span>
            <button
              type="button"
              onClick={() => void send()}
              disabled={!canSend}
              aria-label="보내기"
              className="interactive grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:active:scale-100"
            >
              <Icon name="arrow_upward" size={17} />
            </button>
          </div>
        </div>
        <p className="mx-auto mt-1.5 max-w-2xl text-center text-[11px] text-muted-foreground">
          RepoLM의 답변은 부정확할 수 있으니 출처를 확인하세요.
        </p>
      </div>
    </>
  );
}
