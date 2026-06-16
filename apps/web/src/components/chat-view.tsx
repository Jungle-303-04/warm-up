"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useChatScroll } from "../hooks/use-chat-scroll";
import { askNotebook, listNotebookChatMessages } from "../lib/api";
import { SUGGESTIONS } from "../lib/fixtures";
import { scopeFilePaths } from "../lib/indexing";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type {
  ChatMessage,
  Citation,
  NotebookChatCitation,
  NotebookChatMessage,
  NotebookChatResponse,
} from "../lib/types";
import { ChatEmpty } from "./chat-empty";
import { ChatMessageView } from "./chat-message";
import { Icon } from "./icon";

const makeId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

// 백엔드 인용 → UI 인용.
function toCitations(citations: NotebookChatCitation[]): Citation[] {
  return citations.map((c) => ({
    sourceId: c.source_id,
    sourceName: c.source_title,
    path: c.path ?? undefined,
    snippet: c.snippet,
  }));
}

// 백엔드 응답 → 어시스턴트 메시지. 인용이 없으면 보류(notice)로 본다.
function toAssistantMessage(response: NotebookChatResponse, animate: boolean): ChatMessage {
  return {
    id: makeId(),
    role: "assistant",
    content: response.answer,
    kind: response.citations.length > 0 ? "answer" : "notice",
    citations: toCitations(response.citations),
    animate,
  };
}

// 저장된 대화 기록 → 메시지 목록(복원분은 타이핑 없이 즉시 표시).
function historyToMessages(messages: NotebookChatMessage[]): ChatMessage[] {
  return messages.map((m) => ({
    id: m.id || makeId(),
    role: m.role,
    content: m.content,
    kind:
      m.role === "assistant" && m.citations.length === 0 ? "notice" : "answer",
    citations: m.role === "assistant" ? toCitations(m.citations) : [],
    animate: false,
  }));
}

function draftKey(notebookId: string) {
  return `repolm.chatDraft.${notebookId}`;
}

export function ChatView() {
  const scopeCount = useWorkspace(selectScopeCount);
  const sourceCount = useWorkspace((s) => s.sources.length);
  const notebookId = useWorkspace((s) => s.notebookId);
  const selectedSourceIds = useWorkspace((s) => s.selectedSourceIds);
  const sources = useWorkspace((s) => s.sources);
  const indexProgress = useWorkspace((s) => s.indexProgress);
  const selectedFilePaths = useWorkspace((s) => s.selectedFilePaths);

  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [queuedQuestions, setQueuedQuestions] = useState<string[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const selectedSourceIdList = useMemo(() => [...selectedSourceIds], [selectedSourceIds]);
  const allSourcesSelected = sourceCount > 0 && scopeCount === sourceCount;
  // 답변 범위 안의 repo 소스 id(파일 단위 범위 계산용).
  const scopeRepoSourceIds = useMemo(
    () =>
      sources
        .filter((s) => s.kind === "repo" && selectedSourceIds.has(s.id))
        .map((s) => s.id),
    [sources, selectedSourceIds],
  );
  const canSend = query.trim().length > 0 && scopeCount > 0 && !!notebookId;

  // 메시지 변화/타이핑 진행/대기 상태에 맞춰 하단 고정 스크롤.
  const { scrollRef, onScroll } = useChatScroll([messages, pendingQuestion]);

  // 클라이언트 로캘 기준의 세션 날짜.
  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // 대화 기록 로드.
  useEffect(() => {
    if (!notebookId) return;
    let active = true;
    setLoadingHistory(true);
    setHistoryError(null);
    listNotebookChatMessages(notebookId)
      .then((history) => {
        if (active) setMessages(historyToMessages(history.messages));
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

  // 입력 초안 복원/저장.
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
      // repo 파일 부분 선택이 있을 때만 file_paths를 보내 답변 범위를 좁힌다.
      const filePaths = scopeFilePaths(scopeRepoSourceIds, indexProgress, selectedFilePaths);
      const controller = new AbortController();
      abortRef.current = controller;
      setPendingQuestion(question);
      setSending(true);
      try {
        const response = await askNotebook(
          notebookId,
          question,
          sourceIds,
          filePaths,
          controller.signal,
        );
        setMessages((prev) => [...prev, toAssistantMessage(response, true)]);
      } catch (error) {
        const wasAborted = controller.signal.aborted;
        const message = error instanceof Error ? error.message : "답변 요청 실패";
        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: "assistant",
            kind: "notice",
            citations: [],
            animate: false,
            content: wasAborted
              ? "진행 중인 답변 생성을 중지했습니다."
              : `답변을 가져오지 못했습니다. ${message}`,
          },
        ]);
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        setPendingQuestion(null);
        setSending(false);
      }
    },
    [
      allSourcesSelected,
      indexProgress,
      notebookId,
      scopeCount,
      scopeRepoSourceIds,
      selectedFilePaths,
      selectedSourceIdList,
    ],
  );

  // 전송 중 들어온 질문은 큐로 모았다가 순차 처리.
  useEffect(() => {
    if (sending || queuedQuestions.length === 0) return;
    const [next, ...rest] = queuedQuestions;
    setQueuedQuestions(rest);
    void runQuestion(next);
  }, [queuedQuestions, runQuestion, sending]);

  const send = useCallback(
    (text = query) => {
      const question = text.trim();
      if (!question || scopeCount === 0 || !notebookId) return;

      setQuery("");
      // 사용자 메시지를 즉시 목록에 추가(낙관적).
      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: "user", kind: "answer", citations: [], content: question },
      ]);

      if (sending) {
        setQueuedQuestions((prev) => [...prev, question]);
        return;
      }
      void runQuestion(question);
    },
    [notebookId, query, runQuestion, scopeCount, sending],
  );

  const stopCurrent = () => {
    abortRef.current?.abort();
    setQueuedQuestions([]);
  };

  // 마지막 사용자 질문으로 재생성.
  const regenerate = () => {
    if (sending) return;
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser) void send(lastUser.content);
  };

  const lastAssistantId = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant")?.id,
    [messages],
  );

  // 소스 0개: 빈 채팅 대신 온보딩 히어로를 보여준다.
  if (sourceCount === 0 && messages.length === 0 && !loadingHistory) return <ChatEmpty />;

  return (
    <>
      <div ref={scrollRef} onScroll={onScroll} className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-6 py-5">
          {/* 헤더 카드 */}
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
              답변에는 항상 출처(파일·라인)가 따라옵니다.
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

          {/* 추천 질문: 클릭 시 입력창을 채우고, 더블클릭 시 바로 전송. */}
          {messages.length === 0 && !loadingHistory ? (
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
                    onClick={() => send(q)}
                    disabled={scopeCount === 0}
                    className="interactive group flex w-full items-center gap-3 rounded-xl border border-border bg-card px-3.5 py-2.5 text-left text-[13px] text-foreground hover:border-primary/40 hover:bg-secondary hover:shadow-elev-1 disabled:cursor-not-allowed disabled:opacity-50"
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

          {/* 대화 메시지 */}
          <div className="mt-6 space-y-5">
            {messages.map((message) => (
              <ChatMessageView
                key={message.id}
                message={message}
                onRegenerate={
                  message.role === "assistant" && message.id === lastAssistantId && !sending
                    ? regenerate
                    : undefined
                }
              />
            ))}

            {/* 생각 중 표시(점 애니메이션). */}
            {sending && pendingQuestion ? (
              <div className="message-in flex items-center gap-2.5 text-[12.5px] text-muted-foreground">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
                  <Icon name="hub" size={15} />
                </span>
                <div className="rounded-2xl rounded-tl-md border border-border bg-card px-3 py-2 shadow-elev-1">
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
            ) : null}
          </div>
        </div>
      </div>

      {/* 하단 입력바 */}
      <div className="shrink-0 px-5 pb-4">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-[24px] border border-border bg-card px-2.5 py-2 shadow-elev-2 focus-within:border-primary/50">
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
            disabled={scopeCount === 0}
            placeholder={
              scopeCount === 0
                ? "왼쪽에서 소스를 선택하세요"
                : sending
                  ? "다음 질문을 입력하면 대기열에 추가됩니다"
                  : "무엇이든 물어보세요 (Enter 전송 · Shift+Enter 줄바꿈)"
            }
            aria-label="메시지 입력"
            className="max-h-32 flex-1 resize-none self-center bg-transparent py-1.5 pl-2 text-[13px] leading-relaxed outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed"
          />
          <div className="flex shrink-0 items-center gap-2 self-end pb-0.5">
            <span className="hidden items-center gap-1 text-[11px] text-muted-foreground sm:inline-flex">
              <Icon name="description" size={12} />
              소스 {scopeCount}/{sourceCount}개
            </span>
            <button
              type="button"
              onClick={() => send()}
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
