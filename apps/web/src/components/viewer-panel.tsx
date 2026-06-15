"use client";

import { SOURCE_KINDS, SOURCES } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { Source } from "../lib/types";
import { Icon } from "./icon";
import { MarkdownView } from "./markdown-view";

function EmptyState() {
  return (
    <div className="grid flex-1 place-items-center px-6 text-center">
      <div className="max-w-xs">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-secondary text-muted-foreground">
          <Icon name="description" size={22} />
        </span>
        <p className="mt-3 text-[14px] font-semibold">열어 볼 소스를 선택하세요</p>
        <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
          왼쪽 소스 목록에서 항목을 클릭하면 여기서 원문을 확인할 수 있습니다. 체크박스는
          대화 답변의 범위를 정합니다.
        </p>
      </div>
    </div>
  );
}

function SourceBody({ source }: { source: Source }) {
  if (source.kind === "repo") {
    return (
      <>
        <div className="mb-4 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-medium text-muted-foreground">브랜치</span>
          {(source.branches ?? []).map((b) => (
            <span
              key={b}
              className="rounded-full border border-border bg-secondary/60 px-2 py-0.5 text-[11px]"
            >
              {b}
            </span>
          ))}
        </div>
        <article className="markdown-body text-[14px] leading-relaxed">
          <MarkdownView source={source.content ?? ""} />
        </article>
      </>
    );
  }
  if (source.kind === "md") {
    return (
      <article className="markdown-body text-[14px] leading-relaxed">
        <MarkdownView source={source.content ?? ""} />
      </article>
    );
  }
  // text · pdf — 추출 텍스트를 그대로 표시
  return (
    <>
      {source.kind === "pdf" ? (
        <div className="mb-3 flex items-center gap-1.5 rounded-lg bg-secondary/60 px-3 py-2 text-[11px] text-muted-foreground">
          <Icon name="picture_as_pdf" size={14} />
          PDF는 추출 텍스트로 인덱싱·표시됩니다.
        </div>
      ) : null}
      <pre className="whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed">
        {source.content ?? ""}
      </pre>
    </>
  );
}

export function ViewerPanel() {
  const focusedId = useWorkspace((s) => s.focusedSourceId);
  const selected = useWorkspace((s) => s.selected);
  const toggleSource = useWorkspace((s) => s.toggleSource);

  const source = SOURCES.find((s) => s.id === focusedId) ?? null;
  if (!source) return <EmptyState />;

  const cfg = SOURCE_KINDS[source.kind];
  const inScope = !!selected[source.id];

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex shrink-0 items-center gap-2 border-b border-border px-4 py-2.5">
        <span
          className="grid h-7 w-7 shrink-0 place-items-center rounded-md"
          style={{ background: cfg.chipBg, color: cfg.chipFg }}
        >
          <Icon name={cfg.icon} size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold leading-tight">{source.name}</p>
          <p className="text-[11px] text-muted-foreground">{cfg.label}</p>
        </div>
        <button
          type="button"
          onClick={() => toggleSource(source.id)}
          aria-pressed={inScope}
          className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[12px] transition-colors ${
            inScope
              ? "border-primary/30 bg-primary/10 text-primary"
              : "border-border text-muted-foreground hover:bg-secondary"
          }`}
        >
          <Icon name={inScope ? "check_circle" : "add_circle"} size={14} />
          {inScope ? "범위에 포함됨" : "범위에 추가"}
        </button>
        {source.externalUrl ? (
          <a
            href={source.externalUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-secondary"
          >
            <Icon name="north_east" size={14} /> GitHub
          </a>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-5 py-6">
          <SourceBody source={source} />
        </div>
      </div>
    </div>
  );
}
