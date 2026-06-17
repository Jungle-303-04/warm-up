"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useChatScroll } from "../hooks/use-chat-scroll";
import { askNotebook, listNotebookChatMessages, clearNotebookChatMessages } from "../lib/api";
import { SUGGESTIONS } from "../lib/fixtures";
import { scopeFilePaths } from "../lib/indexing";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type {
  ChatMessage,
  Citation,
  GeneratableArtifactType,
  NotebookChatCitation,
  NotebookChatMessage,
  NotebookChatResponse,
} from "../lib/types";
import { ChatEmpty } from "./chat-empty";
import { ChatMessageView } from "./chat-message";
import { Icon } from "./icon";
import { Button } from "./ui/button";

const makeId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

// 채팅에서 "레포를 UML/ERD/의존성 그래프로 그려줘" 류 요청을 감지해, 텍스트 답변
// 대신 스튜디오 산출물(다이어그램)을 생성하고 뷰어에서 열도록 라우팅한다.
// 정의/개념 질문("UML이 뭐야")은 제외한다(시각화 의도가 아님).
const DIAGRAM_LABELS: Record<"uml" | "erd" | "dependency", string> = {
  uml: "UML 클래스 다이어그램",
  erd: "ERD",
  dependency: "의존성 그래프",
};

const VISUALIZE_CUE =
  /(그려|그림|만들어|생성|시각화|보여|작성|도식|그래프로|diagram|draw|generate|create|visuali[sz]e|render)/i;
const DEFINITIONAL_CUE = /(뭐야|뭔가요|무엇|이란|개념|차이|장단점|what\s+is|difference)/i;
const DIAGRAM_WORD = /(다이어그램|diagram|그래프|graph)/i;

function detectDiagramIntent(question: string): "uml" | "erd" | "dependency" | null {
  if (DEFINITIONAL_CUE.test(question)) return null;
  // "시각화/그려/생성" 같은 동사 단서나 "다이어그램/그래프" 명사가 있어야 한다.
  if (!VISUALIZE_CUE.test(question) && !DIAGRAM_WORD.test(question)) return null;
  if (/\berd\b|엔티티\s*관계|entity[\s-]*relationship|테이블\s*관계|스키마\s*다이어그램/i.test(question))
    return "erd";
  if (/uml|클래스\s*다이어그램|class\s*diagram|클래스\s*관계|클래스도/i.test(question)) return "uml";
  if (/의존성|dependency|모듈\s*의존|import\s*관계/i.test(question)) return "dependency";
  return null;
}

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
  const generateArtifact = useWorkspace((s) => s.generateArtifact);
  const addNote = useWorkspace((s) => s.addNote);
  // 센터 바(탭 줄)의 초기화/메모저장 버튼이 보내는 1회성 명령 신호.
  const resetChatSignal = useWorkspace((s) => s.resetChatSignal);
  const saveChatSignal = useWorkspace((s) => s.saveChatSignal);
  const setChatMessageCount = useWorkspace((s) => s.setChatMessageCount);

  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [queuedQuestions, setQueuedQuestions] = useState<string[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // 단일 비행(single-flight) 가드: 한 번에 한 질문만 처리되도록 보장한다.
  // sending 상태는 비동기로 갱신돼 효과/직접호출이 겹칠 수 있으므로 ref로 즉시 잠근다.
  const runningRef = useRef(false);

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
  const { scrollRef, onScroll, scrollToBottom } = useChatScroll([messages, pendingQuestion]);

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
      // 이미 처리 중이면 중복 실행 금지(직접 호출/큐 효과 중복 방지).
      if (runningRef.current) return;
      runningRef.current = true;

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
        runningRef.current = false; // 잠금 해제 → 큐의 다음 질문 처리 가능.
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

  // 큐 단일 드레인: 모든 질문은 큐에 쌓이고 여기서 한 번에 하나씩만 꺼내 처리한다.
  // - sending=false(앞 질문 완료)일 때만 다음 질문을 시작 → 완료 후 자동으로 다음 항목 처리.
  // - runningRef는 sending 상태 갱신 지연/효과 중복으로 인한 동시 실행을 막는 하드 가드.
  // 직접 호출 경로를 없애 "한 질문당 답변 1개"를 보장한다.
  useEffect(() => {
    if (sending || runningRef.current || queuedQuestions.length === 0) return;
    const next = queuedQuestions[0];
    // 먼저 큐에서 제거한 뒤 실행(같은 질문 재진입 방지).
    setQueuedQuestions((prev) => prev.slice(1));
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

      // 다이어그램(UML/ERD/의존성) 요청이면 텍스트 답변 대신 스튜디오 산출물로
      // 생성하고 가운데 "뷰어" 탭에서 열어 정식 다이어그램으로 보여준다.
      const diagram = detectDiagramIntent(question);
      if (diagram) {
        const label = DIAGRAM_LABELS[diagram];
        void generateArtifact(diagram, selectedSourceIdList).then((created) => {
          // 성공 시 store가 뷰어 탭으로 전환하므로 별도 안내가 필요 없다.
          // 실패 시에는 채팅에 안내 메시지를 남긴다(이 경로에선 탭 전환이 없다).
          if (!created) {
            setMessages((prev) => [
              ...prev,
              {
                id: makeId(),
                role: "assistant",
                kind: "notice",
                citations: [],
                animate: false,
                content: `${label} 생성에 실패했습니다. 잠시 후 다시 시도하거나 오른쪽 스튜디오에서 직접 생성해 주세요.`,
              },
            ]);
          }
        });
        return;
      }

      // 항상 큐에 넣고, 위의 단일 드레인 효과가 순차 처리한다(직접 실행 금지).
      setQueuedQuestions((prev) => [...prev, question]);
    },
    [generateArtifact, notebookId, query, scopeCount, selectedSourceIdList],
  );

  const stopCurrent = () => {
    abortRef.current?.abort();
    setQueuedQuestions([]);
  };

  // 대화 초기화: 백엔드 API를 통해 메시지 영속 삭제
  // 진행 중 요청 중단 + 화면 메시지/대기열/입력 초안(localStorage) 클리어.
  const resetConversation = () => {
    abortRef.current?.abort();
    setQueuedQuestions([]);
    setMessages([]);
    setQuery("");
    setHistoryError(null);
    if (notebookId) {
      void clearNotebookChatMessages(notebookId).catch((err) => {
        console.error("대화 삭제 API 실패:", err);
      });
      try {
        localStorage.removeItem(draftKey(notebookId));
      } catch {
        // 초안 삭제 실패는 초기화를 막지 않는다.
      }
    }
  };

  // 지금까지의 대화를 마크다운 메모로 정리해 스튜디오에 저장한다.
  // 저장된 메모는 "소스로 추가"로 임베딩되어 이후 답변의 근거(RAG)로도 쓸 수 있다.
  const saveConversationAsNote = () => {
    const real = messages.filter((m) => m.kind !== "notice");
    if (real.length === 0) return;
    const lines: string[] = [`# 대화 정리 — ${today}`, ""];
    for (const m of real) {
      if (m.role === "user") {
        lines.push("## 질문", "", m.content.trim(), "");
      } else {
        lines.push("**답변**", "", m.content.trim(), "");
        if (m.citations.length > 0) {
          const refs = m.citations
            .map((c) => (c.path ? c.path.split("/").pop() || c.path : c.sourceName))
            .join(", ");
          lines.push(`> 출처: ${refs}`, "");
        }
      }
    }
    const content = lines.join("\n");
    void addNote({ title: `대화 정리 · ${today}`, content }).then((created) => {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          kind: "notice",
          citations: [],
          animate: false,
          content: created
            ? '이번 대화를 메모로 저장했습니다. 오른쪽 스튜디오에서 "소스로 추가"하면 임베딩되어 이후 답변의 근거로도 쓸 수 있어요.'
            : "대화 메모 저장에 실패했습니다.",
        },
      ]);
    });
  };

  // 센터 바의 초기화/메모저장 버튼은 store 신호(nonce)로 전달된다.
  // 마운트 직후(초기 0값) 오작동을 막기 위해 첫 실행은 건너뛴다.
  const resetSignalInit = useRef(true);
  useEffect(() => {
    if (resetSignalInit.current) {
      resetSignalInit.current = false;
      return;
    }
    resetConversation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetChatSignal]);

  const saveSignalInit = useRef(true);
  useEffect(() => {
    if (saveSignalInit.current) {
      saveSignalInit.current = false;
      return;
    }
    saveConversationAsNote();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saveChatSignal]);

  // 센터 바 버튼의 활성/비활성 판단용으로 메시지 개수를 store에 공개한다.
  useEffect(() => {
    setChatMessageCount(messages.length);
  }, [messages.length, setChatMessageCount]);

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
      <div ref={scrollRef} onScroll={onScroll} className="flex-1 overflow-y-auto scroll-smooth">
        <div className="w-full px-6 py-5">
          {/* 헤더 카드 */}
          <div className="rounded-2xl border border-border/50 bg-card/80 p-5">
            <div className="flex items-center gap-3">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary">
                <Icon name="hub" size={16} />
              </span>
              <div className="min-w-0 flex-1">
                <h1 className="truncate text-[15px] font-semibold tracking-tight">RepoLM 대화</h1>
                <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                  소스 {sourceCount}개 연결됨 · {today}
                </p>
              </div>
              {/* 기준/초기화/메모저장 컨트롤은 상단 탭 바(center-panel)로 이동했다. */}
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
              연결된 저장소·문서를 근거로 질문에 답하고, 코드와 문서가 어긋난 부분을 찾습니다.
              답변에는 항상 출처(파일·라인)가 따라옵니다.
            </p>
          </div>

          {loadingHistory || historyError ? (
            <div className="mt-2.5 flex items-center gap-2 rounded-lg border border-border/50 bg-secondary/60 px-3 py-2 text-[11px] text-muted-foreground">
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
                    className="transition-all duration-150 group flex w-full items-center gap-3 rounded-xl border border-border/40 bg-card/50 px-3.5 py-2.5 text-left text-[13px] text-foreground hover:border-primary/30 hover:bg-secondary/80 disabled:cursor-not-allowed disabled:opacity-40"
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
          <div className="mt-6 space-y-4">
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
              <div className="transition-all duration-200 flex items-center gap-2.5 text-[12px] text-muted-foreground animate-in fade-in slide-in-from-bottom-2">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                  <Icon name="hub" size={14} />
                </span>
                <div className="rounded-2xl rounded-tl-md border border-border/50 bg-card/80 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1" aria-hidden>
                      <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                    <span>근거를 찾고 답변을 조립하는 중</span>
                    <Button
                      variant="ghost"
                      size="xs"
                      icon="stop_circle"
                      onClick={stopCurrent}
                      className="ml-1 bg-secondary"
                    >
                      중지
                    </Button>
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

      {/* 하단 입력바 - 중앙 플로팅 알약형 캡슐 */}
      <div className="shrink-0 px-4 pb-4 pt-2">
        <div className="flex w-full items-end gap-2.5 rounded-3xl border border-border/50 bg-card/90 px-4 py-2.5 shadow-sm focus-within:border-primary/40 focus-within:ring-1 focus-within:ring-primary/15 transition-all duration-150 backdrop-blur-sm">
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
                : "질문하거나 창작하세요"
            }
            aria-label="메시지 입력"
            className="max-h-32 flex-1 resize-none self-center bg-transparent py-1 pl-1 text-[13px] leading-relaxed outline-none placeholder:text-muted-foreground/60 disabled:cursor-not-allowed"
          />
          <div className="flex shrink-0 items-center gap-2 self-end pb-0.5">
            {scopeCount > 0 ? (
              <span className="inline-flex items-center gap-1 text-[10px] font-medium text-muted-foreground bg-secondary/80 px-2 py-0.5 rounded-full">
                소스 {scopeCount}개
              </span>
            ) : null}
            <button
              type="button"
              onClick={() => send()}
              disabled={!canSend}
              aria-label="보내기"
              className="transition-all duration-150 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground hover:opacity-90 active:scale-95 disabled:opacity-30"
            >
              <Icon name="arrow_forward" size={16} />
            </button>
          </div>
        </div>
        <p className="mt-2 w-full text-center text-[10px] text-muted-foreground/50">
          RepoLM의 답변은 부정확할 수 있으니 반드시 출처를 확인하세요.
        </p>
      </div>
    </>
  );
}
