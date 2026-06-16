"use client";

import { useState } from "react";

import { useTypewriter } from "../hooks/use-typewriter";
import { useWorkspace } from "../lib/store";
import type { ChatMessage, Citation } from "../lib/types";
import { CitationChip } from "./citation-chip";
import { Icon } from "./icon";
import { MarkdownView } from "./markdown-view";

// 인용 라벨: 경로 우선, 없으면 소스명.
function citationLabel(c: Citation): string {
  return c.path ?? c.sourceName;
}

function CitationChips({ citations }: { citations: Citation[] }) {
  const openSource = useWorkspace((s) => s.openSource);
  const openFile = useWorkspace((s) => s.openFile);
  const open = (c: Citation) =>
    c.path ? openFile(c.sourceId, c.path) : openSource(c.sourceId);

  return (
    <div className="flex flex-wrap gap-1.5">
      {citations.map((c, i) => (
        <CitationChip
          key={`${c.sourceId}-${i}`}
          index={i + 1}
          label={citationLabel(c)}
          onClick={() => open(c)}
        />
      ))}
    </div>
  );
}

// 사용자 메시지: 우측 primary 말풍선.
function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="w-fit max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-[13px] leading-relaxed text-primary-foreground shadow-elev-1">
        {content}
      </div>
    </div>
  );
}

// 어시스턴트 메시지: 좌측 아바타 + 카드. 본문은 markdown, 도착분은 타이핑 효과.
function AssistantBubble({
  message,
  onRegenerate,
}: {
  message: ChatMessage;
  onRegenerate?: () => void;
}) {
  const { text, done, stop } = useTypewriter(message.content, Boolean(message.animate));
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);
  const addNote = useWorkspace((s) => s.addNote);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // 복사 실패는 조용히 무시.
    }
  };

  // 이 답변을 스튜디오 메모(kind:note)로 저장. 제목은 본문 첫 줄에서 추린다.
  const saveToNote = () => {
    const firstLine = message.content.trim().split("\n")[0]?.trim() ?? "";
    const title = firstLine ? firstLine.slice(0, 40) : "대화 메모";
    addNote({ title, detail: "대화에서 저장 · 방금 전", body: message.content });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  if (message.kind === "notice") {
    return (
      <div className="flex gap-2.5">
        <Avatar />
        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2.5 rounded-2xl rounded-tl-md border border-border bg-secondary px-3 py-2.5 text-[12.5px] leading-relaxed text-muted-foreground">
            <Icon name="report" size={15} className="mt-0.5 shrink-0 text-primary" />
            <span>{message.content}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="group flex gap-2.5">
      <Avatar />
      <div className="min-w-0 flex-1">
        <div className="rounded-2xl rounded-tl-md border border-border bg-card px-3.5 py-2.5 shadow-elev-1">
          <MarkdownView source={text} />
          {/* 타이핑 끝난 뒤에만 인용칩 노출. */}
          {done && message.citations.length > 0 ? (
            <div className="mt-3">
              <CitationChips citations={message.citations} />
            </div>
          ) : null}
        </div>
        {/* 액션 줄: 호버 노출(복사·재생성·타이핑 건너뛰기). */}
        <div className="mt-1 flex items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
          <ActionButton icon={copied ? "check" : "copy"} label="복사" onClick={copy} />
          <ActionButton
            icon={saved ? "check" : "save_note"}
            label="메모에 저장"
            onClick={saveToNote}
          />
          {onRegenerate ? (
            <ActionButton icon="progress_activity" label="재생성" onClick={onRegenerate} />
          ) : null}
          {!done ? <ActionButton icon="stop_circle" label="타이핑 건너뛰기" onClick={stop} /> : null}
        </div>
      </div>
    </div>
  );
}

function Avatar() {
  return (
    <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent text-accent-foreground">
      <Icon name="hub" size={15} />
    </span>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
}: {
  icon: string;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="interactive grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
    >
      <Icon name={icon} size={14} />
    </button>
  );
}

export function ChatMessageView({
  message,
  onRegenerate,
}: {
  message: ChatMessage;
  onRegenerate?: () => void;
}) {
  return (
    <div className="message-in">
      {message.role === "user" ? (
        <UserBubble content={message.content} />
      ) : (
        <AssistantBubble message={message} onRegenerate={onRegenerate} />
      )}
    </div>
  );
}
