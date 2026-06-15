"use client";

import { useState } from "react";

import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";

// ── 더미 데이터 (API 연동 전 셸 표시용) ─────────────────────────────
type Source = {
  id: string;
  name: string;
  kind: "repo" | "doc" | "link";
  progress: number; // 0~100, 100=완료
  status?: string;
};

const SOURCES: Source[] = [
  { id: "a", name: "team/api", kind: "repo", progress: 92 },
  { id: "b", name: "team/web", kind: "repo", progress: 38, status: "동기화중" },
  { id: "c", name: "docs/architecture.md", kind: "doc", progress: 100 },
  { id: "d", name: "https://wiki…", kind: "link", progress: 100 },
];

const THREADS = ["인증 흐름 점검", "스프린트 계획", "ERD 리뷰"];

const STUDIO = [
  { icon: "account_tree", label: "UML 생성" },
  { icon: "schema", label: "ERD 생성" },
  { icon: "checklist", label: "계획 생성" },
  { icon: "calendar_month", label: "일정 요약" },
];

const SOURCE_ICON: Record<Source["kind"], string> = {
  repo: "folder_code",
  doc: "description",
  link: "link",
};

// ── 작은 조립 단위 ──────────────────────────────────────────────────
function IconButton({ name, label }: { name: string; label: string }) {
  return (
    <button
      type="button"
      title={label}
      className="grid h-8 w-8 place-items-center rounded-md text-muted transition-colors hover:bg-elev hover:text-ink"
    >
      <Icon name={name} className="text-[20px]" />
    </button>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="px-1 text-[11px] font-medium uppercase tracking-wide text-faint">
      {children}
    </p>
  );
}

function PanelHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="flex h-11 items-center justify-between border-b border-edge px-3">
      <span className="text-[13px] font-medium">{title}</span>
      {action}
    </div>
  );
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-1 w-full overflow-hidden rounded-full bg-edge">
      <div className="h-full rounded-full bg-brand" style={{ width: `${value}%` }} />
    </div>
  );
}

function SourceRow({
  source,
  checked,
  onToggle,
}: {
  source: Source;
  checked: boolean;
  onToggle: () => void;
}) {
  const done = source.progress >= 100;
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-elev"
    >
      <Icon
        name={checked ? "check_box" : "check_box_outline_blank"}
        className={`text-[18px] ${checked ? "text-brand" : "text-faint"}`}
      />
      <Icon name={SOURCE_ICON[source.kind]} className="text-[18px] text-muted" />
      <span className="flex-1 truncate text-[13px]">{source.name}</span>
      {done ? null : (
        <span className="w-12 shrink-0">
          <ProgressBar value={source.progress} />
        </span>
      )}
    </button>
  );
}

function CitationChip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-weak px-2 py-0.5 text-[11px] font-medium text-brand">
      <Icon name="play_arrow" className="text-[13px]" />
      {label}
    </span>
  );
}

function ProposalCard() {
  const [decision, setDecision] = useState<"none" | "approved" | "rejected">("none");
  return (
    <div className="rounded-xl border border-edge bg-elev p-3">
      <p className="text-[11px] text-muted">제안 · 관련 코드 · confidence 0.86</p>
      <p className="mt-1 text-[13px]">docs/auth.md 가 토큰 만료 케이스를 다루지 않습니다.</p>
      <div className="mt-2 flex items-center gap-2">
        {decision === "none" ? (
          <>
            <button
              type="button"
              onClick={() => setDecision("approved")}
              className="rounded-md bg-ok-weak px-3 py-1 text-[12px] font-medium text-ok"
            >
              승인
            </button>
            <button
              type="button"
              onClick={() => setDecision("rejected")}
              className="rounded-md bg-danger-weak px-3 py-1 text-[12px] font-medium text-danger"
            >
              반려
            </button>
          </>
        ) : (
          <span className="text-[12px] text-muted">
            {decision === "approved" ? "승인됨 · 이슈로 발행 예정" : "반려됨"}
          </span>
        )}
      </div>
    </div>
  );
}

function SuggestChip({ children }: { children: React.ReactNode }) {
  return (
    <button
      type="button"
      className="rounded-full border border-edge px-3 py-1 text-[12px] text-muted transition-colors hover:bg-elev hover:text-ink"
    >
      {children}
    </button>
  );
}

// ── 패널 ────────────────────────────────────────────────────────────
function SourcesPanel() {
  const [selected, setSelected] = useState<Record<string, boolean>>(
    Object.fromEntries(SOURCES.map((s) => [s.id, true])),
  );
  return (
    <aside className="flex w-72 shrink-0 flex-col overflow-hidden rounded-xl border border-edge bg-panel">
      <PanelHeader
        title="Sources"
        action={
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded-full bg-elev px-2.5 py-1 text-[12px] text-ink transition-colors hover:bg-edge"
          >
            <Icon name="add" className="text-[16px]" /> 추가
          </button>
        }
      />
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-0.5">
          {SOURCES.map((s) => (
            <SourceRow
              key={s.id}
              source={s}
              checked={!!selected[s.id]}
              onToggle={() => setSelected((p) => ({ ...p, [s.id]: !p[s.id] }))}
            />
          ))}
        </div>
        <div className="my-3 border-t border-edge" />
        <SectionLabel>Threads</SectionLabel>
        <div className="mt-1 space-y-0.5">
          {THREADS.map((t) => (
            <button
              key={t}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] transition-colors hover:bg-elev"
            >
              <Icon name="chat_bubble" className="text-[16px] text-faint" />
              <span className="flex-1 truncate">{t}</span>
            </button>
          ))}
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] text-brand transition-colors hover:bg-elev"
          >
            <Icon name="add" className="text-[16px]" /> 새 대화
          </button>
        </div>
      </div>
    </aside>
  );
}

const TABS = ["Chat", "Board", "Viewer"] as const;

function ChatPanel() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Chat");
  return (
    <section className="flex flex-1 flex-col overflow-hidden rounded-xl border border-edge bg-panel">
      <div className="flex h-11 items-center gap-1 border-b border-edge px-3">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-md px-2.5 py-1 text-[13px] transition-colors ${
              tab === t ? "bg-elev font-medium text-ink" : "text-muted hover:text-ink"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Chat" ? (
        <>
          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
            <div className="max-w-[80%]">
              <p className="text-[13px] leading-relaxed">
                로그인 실패는 JWT 만료가 가장 흔한 원인입니다. 인증 미들웨어에서 만료
                토큰을 401로 처리합니다.
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                <CitationChip label="api/auth.py:12-18 @a1b2" />
                <CitationChip label="docs/auth.md @a1b2" />
              </div>
            </div>
            <ProposalCard />
            <div className="flex flex-wrap gap-2">
              <SuggestChip>토큰 갱신 흐름은?</SuggestChip>
              <SuggestChip>관련 PR 보기</SuggestChip>
              <SuggestChip>스테일 링크 점검</SuggestChip>
            </div>
          </div>
          <div className="border-t border-edge p-3">
            <div className="flex items-center gap-2 rounded-full border border-edge bg-elev px-3 py-2">
              <input
                placeholder="질문을 입력하세요…"
                className="flex-1 bg-transparent text-[13px] outline-none placeholder:text-faint"
              />
              <button
                type="button"
                className="grid h-7 w-7 place-items-center rounded-full bg-brand text-white"
              >
                <Icon name="arrow_upward" className="text-[18px]" />
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="grid flex-1 place-items-center text-[13px] text-faint">
          {tab} 뷰 — 추후 구현
        </div>
      )}
    </section>
  );
}

function StudioPanel() {
  return (
    <aside className="flex w-80 shrink-0 flex-col overflow-hidden rounded-xl border border-edge bg-panel">
      <PanelHeader title="Studio" />
      <div className="flex-1 overflow-y-auto p-3">
        <div className="space-y-2">
          {STUDIO.map((b) => (
            <button
              key={b.label}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg border border-edge bg-elev px-3 py-2 text-[13px] transition-colors hover:border-brand hover:text-brand"
            >
              <Icon name={b.icon} className="text-[18px]" />
              {b.label}
            </button>
          ))}
        </div>
        <div className="my-3 border-t border-edge" />
        <SectionLabel>저장된 노트</SectionLabel>
        <div className="mt-1 space-y-0.5">
          {["도메인 ERD v2", "인증 시퀀스 UML"].map((n) => (
            <button
              key={n}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-[13px] transition-colors hover:bg-elev"
            >
              <Icon name="article" className="text-[16px] text-faint" />
              <span className="flex-1 truncate">{n}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-edge px-4">
      <button
        type="button"
        className="inline-flex items-center gap-2 rounded-md px-2 py-1 text-[14px] font-medium transition-colors hover:bg-elev"
      >
        <Icon name="hub" className="text-[20px] text-brand" />
        RepoLM · 워크스페이스
        <Icon name="unfold_more" className="text-[18px] text-faint" />
      </button>
      <div className="flex items-center gap-1">
        <button
          type="button"
          className="mr-1 hidden items-center gap-1 rounded-md border border-edge px-2 py-1 text-[12px] text-muted sm:inline-flex"
        >
          <Icon name="search" className="text-[16px]" /> ⌘K
        </button>
        <IconButton name="notifications" label="알림" />
        <ThemeToggle />
        <IconButton name="account_circle" label="계정" />
      </div>
    </header>
  );
}

export function Workspace() {
  return (
    <div className="flex h-screen flex-col bg-bg text-ink">
      <TopBar />
      <main className="flex flex-1 gap-3 overflow-hidden p-3">
        <SourcesPanel />
        <ChatPanel />
        <StudioPanel />
      </main>
    </div>
  );
}
