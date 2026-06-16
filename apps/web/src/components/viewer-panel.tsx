"use client";

import { useEffect, useState } from "react";

import { getFile, getSource } from "../lib/api";
import { SOURCE_KINDS } from "../lib/fixtures";
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
          왼쪽 소스 목록에서 항목을 클릭하면 여기서 원문을 확인할 수 있습니다. 레포는 펼쳐
          파일을 선택하세요. 체크박스는 대화 답변의 범위를 정합니다.
        </p>
      </div>
    </div>
  );
}

// markdown은 렌더, 그 외(text/pdf/추출 파일)는 원문 텍스트로 표시.
function Body({ source, content }: { source: Source | null; content: string }) {
  const isMarkdown = source?.kind === "md";
  if (isMarkdown) {
    return (
      <article className="markdown-body text-[14px] leading-relaxed">
        <MarkdownView source={content} />
      </article>
    );
  }
  return (
    <>
      {source?.kind === "pdf" ? (
        <div className="mb-3 flex items-center gap-1.5 rounded-lg bg-secondary/60 px-3 py-2 text-[11px] text-muted-foreground">
          <Icon name="picture_as_pdf" size={14} />
          PDF는 추출 텍스트로 인덱싱·표시됩니다.
        </div>
      ) : null}
      <pre className="whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed">
        {content}
      </pre>
    </>
  );
}

export function ViewerPanel() {
  const viewer = useWorkspace((s) => s.viewer);
  const notebookId = useWorkspace((s) => s.notebookId);
  const sources = useWorkspace((s) => s.sources);

  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const source = sources.find((s) => s.id === viewer?.sourceId) ?? null;
  const filePath = viewer?.path;

  // viewer 대상이 바뀌면 내용을 로드한다.
  useEffect(() => {
    if (!viewer || !notebookId) return;
    let active = true;
    setLoading(true);
    setError(null);
    setContent("");

    const load = filePath
      ? getFile(notebookId, viewer.sourceId, filePath).then((r) => r.content)
      : getSource(notebookId, viewer.sourceId).then((r) => r.content ?? "");

    load
      .then((c) => active && setContent(c))
      .catch((e) => active && setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [viewer, notebookId, filePath]);

  if (!viewer || !source) return <EmptyState />;

  const cfg = SOURCE_KINDS[source.kind];
  const headerTitle = filePath ?? source.title;
  const headerSub = filePath ? source.title : cfg.label;
  const externalUrl = source.url ?? source.repository_url ?? null;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex shrink-0 items-center gap-2 border-b border-border px-4 py-2.5">
        <span
          className="grid h-7 w-7 shrink-0 place-items-center rounded-md"
          style={{ background: cfg.chipBg, color: cfg.chipFg }}
        >
          <Icon name={filePath ? "file" : cfg.icon} size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold leading-tight">{headerTitle}</p>
          <p className="truncate text-[11px] text-muted-foreground">{headerSub}</p>
        </div>
        {externalUrl ? (
          <a
            href={externalUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-secondary"
          >
            <Icon name="north_east" size={14} /> 열기
          </a>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-5 py-6">
          {loading ? (
            <div className="grid place-items-center py-12 text-muted-foreground">
              <Icon name="progress_activity" size={22} className="animate-spin" />
            </div>
          ) : error ? (
            <p className="text-[13px] text-destructive">{error}</p>
          ) : (
            <Body source={source} content={content} />
          )}
        </div>
      </div>
    </div>
  );
}
