"use client";

import { useCallback, useEffect, useState } from "react";

import { cn } from "../lib/cn";

import { getFile, getSource } from "../lib/api";
import { SOURCE_KINDS } from "../lib/fixtures";
import { classifyLink } from "../lib/links";
import { useWorkspace } from "../lib/store";
import type { Source } from "../lib/types";
import { CodeView } from "./code-view";
import { Icon } from "./icon";
import { MarkdownView } from "./markdown-view";

// 코드 뷰어로 강조해 보여줄 확장자. 마크다운/PDF는 제외(별도 분기).
const CODE_EXTENSIONS = new Set([
  "py",
  "pyi",
  "js",
  "jsx",
  "mjs",
  "cjs",
  "ts",
  "tsx",
  "json",
  "jsonc",
  "html",
  "htm",
  "xml",
  "svg",
  "css",
  "scss",
  "less",
  "sh",
  "bash",
  "zsh",
  "yml",
  "yaml",
  "toml",
  "ini",
  "cfg",
  "sql",
  "go",
  "rs",
  "java",
  "kt",
  "c",
  "h",
  "cpp",
  "cc",
  "hpp",
  "cs",
  "rb",
  "php",
  "swift",
]);

// 파일 경로가 코드 뷰어 대상인지 판정(확장자 기반). 확장자 없는 Dockerfile도 코드 취급.
function isCodePath(filePath?: string): boolean {
  if (!filePath) return false;
  const name = filePath.toLowerCase().split("/").pop() ?? "";
  if (name === "dockerfile") return true;
  const ext = name.includes(".") ? name.split(".").pop()! : "";
  return CODE_EXTENSIONS.has(ext);
}

function EmptyState() {
  return (
    <div className="grid flex-1 place-items-center px-6 text-center">
      <div className="max-w-xs">
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-accent text-accent-foreground">
          <Icon name="description" size={22} />
        </span>
        <p className="mt-3.5 text-[13px] font-semibold">열어 볼 소스를 선택하세요</p>
        <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
          왼쪽 소스 목록에서 항목을 클릭하면 여기서 원문을 확인할 수 있습니다. 레포는 펼쳐
          파일을 선택하세요.
        </p>
      </div>
    </div>
  );
}

// URL 소스 미리보기. 상단에 URL/호스트/제목 카드 + "새 탭에서 열기", 본문은 iframe 임베드 시도.
// 다수 사이트가 X-Frame-Options/CSP로 임베드를 막으므로 onError/타임아웃으로 폴백 안내를 띄운다.
function UrlPreview({ source }: { source: Source }) {
  const url = source.url ?? "";
  const [blocked, setBlocked] = useState(false);
  const [loaded, setLoaded] = useState(false);

  let host = url;
  try {
    host = new URL(url.includes("://") ? url : `https://${url}`).hostname;
  } catch {
    // URL 파싱 실패는 원문 그대로 표시.
  }

  // 일정 시간 안에 load 이벤트가 없으면 차단으로 간주(많은 사이트가 조용히 막는다).
  useEffect(() => {
    if (!url) return;
    setBlocked(false);
    setLoaded(false);
    const t = setTimeout(() => {
      setLoaded((done) => {
        if (!done) setBlocked(true);
        return done;
      });
    }, 4000);
    return () => clearTimeout(t);
  }, [url]);

  return (
    <div className="space-y-3">
      {/* URL/호스트/제목 카드 */}
      <div className="flex items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2.5">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          <Icon name="link" size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12.5px] font-semibold leading-tight">{source.title}</p>
          <p className="truncate text-[11px] text-muted-foreground">{host}</p>
        </div>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="interactive inline-flex shrink-0 items-center gap-1 rounded-full bg-primary px-2.5 py-1 text-[11.5px] font-medium text-primary-foreground hover:opacity-90"
        >
          <Icon name="north_east" size={13} /> 새 탭에서 열기
        </a>
      </div>

      {/* iframe 임베드 시도 + 차단 시 폴백 안내 */}
      {blocked ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border bg-secondary/40 px-4 py-8 text-center">
          <Icon name="public" size={22} className="text-muted-foreground" />
          <p className="text-[12.5px] font-medium">여기서 미리보기를 제공하지 않는 사이트입니다.</p>
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="interactive inline-flex items-center gap-1 rounded-full border border-border px-3 py-1 text-[11.5px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <Icon name="north_east" size={13} /> 새 탭에서 열기
          </a>
        </div>
      ) : (
        <iframe
          src={url}
          title={source.title}
          // 보안: 외부 페이지를 격리 샌드박스로 임베드(스크립트/폼만 허용).
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          referrerPolicy="no-referrer"
          onLoad={() => setLoaded(true)}
          onError={() => setBlocked(true)}
          className="h-[60vh] w-full rounded-xl border border-border bg-card"
        />
      )}
    </div>
  );
}

// markdown은 렌더, 코드 파일은 GitHub풍 코드 뷰어, PDF는 문서형 텍스트 뷰,
// URL은 링크 프리뷰, 그 외(text/추출)는 원문 텍스트로 표시.
function Body({
  source,
  content,
  filePath,
  onLinkClick,
}: {
  source: Source | null;
  content: string;
  filePath?: string;
  onLinkClick: (href: string) => void;
}) {
  // URL 소스(파일 미선택 상태)는 링크 프리뷰로 표시.
  if (source?.kind === "url" && !filePath) {
    return <UrlPreview source={source} />;
  }

  const lowerPath = filePath?.toLowerCase() ?? "";
  const isMarkdown =
    source?.kind === "md" || lowerPath.endsWith(".md") || lowerPath.endsWith(".markdown");
  if (isMarkdown) {
    return (
      <article className="markdown-body text-[13.5px] leading-relaxed">
        <MarkdownView source={content} onLinkClick={onLinkClick} />
      </article>
    );
  }
  // 코드 파일(.py 등)은 줄 번호 거터 + 구문 강조 뷰어로 렌더.
  if (isCodePath(filePath)) {
    return <CodeView content={content} filePath={filePath} />;
  }

  // PDF 소스(파일 미선택): 추출 텍스트를 읽기 좋은 문서형 뷰로 표시(상단 PDF 배지 + 파일명).
  if (source?.kind === "pdf" && !filePath) {
    return (
      <div className="rounded-xl border border-border bg-card px-5 py-4">
        <div className="mb-3 flex items-center gap-2 border-b border-border pb-3">
          <span
            className={cn(
              "grid h-7 w-7 shrink-0 place-items-center rounded-lg",
              "bg-[#FCEBEB] text-[#A32D2D]",
            )}
          >
            <Icon name="picture_as_pdf" size={15} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-[12.5px] font-semibold leading-tight">{source.title}</p>
            <p className="text-[10.5px] text-muted-foreground">PDF · 추출 텍스트</p>
          </div>
        </div>
        <article className="whitespace-pre-wrap break-words font-sans text-[13px] leading-relaxed text-foreground">
          {content}
        </article>
      </div>
    );
  }

  return (
    <pre className="whitespace-pre-wrap break-words font-sans text-[12.5px] leading-relaxed">
      {content}
    </pre>
  );
}

export function ViewerPanel() {
  const viewer = useWorkspace((s) => s.viewer);
  const notebookId = useWorkspace((s) => s.notebookId);
  const sources = useWorkspace((s) => s.sources);
  const openFile = useWorkspace((s) => s.openFile);

  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const source = sources.find((s) => s.id === viewer?.sourceId) ?? null;
  const filePath = viewer?.path;
  const sourceId = viewer?.sourceId;
  const sourceKind = source?.kind;

  // 본문 링크 클릭을 해석해 뷰어 내부 열람으로 치환한다(외부 앱 이동 금지).
  // - external: 새 탭(noreferrer), 내부 네비게이션은 막음.
  // - anchor: 페이지 이동 없이 해당 위치로 스크롤(없으면 무시).
  // - repo-file: 현재 repo 소스이면 해석된 경로의 파일을 viewer로 연다. 그 외 무시.
  const handleLinkClick = useCallback(
    (href: string) => {
      const resolved = classifyLink(href, filePath);
      if (resolved.type === "external") {
        // 외부 절대 URL → 새 탭. 앱 네비게이션은 발생하지 않는다.
        window.open(resolved.href, "_blank", "noreferrer");
        return;
      }
      if (resolved.type === "anchor") {
        // 헤딩 앵커: 가능하면 해당 id로 스크롤, 없으면 조용히 무시.
        const id = decodeURIComponent(resolved.hash.slice(1));
        if (!id) return;
        const el =
          document.getElementById(id) ??
          document.querySelector(`[name="${CSS.escape(id)}"]`);
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      if (resolved.type === "repo-file") {
        // repo 소스 안의 파일만 내부 열람으로 치환. 비repo 소스는 매핑 불가로 무시.
        if (sourceKind === "repo" && sourceId) openFile(sourceId, resolved.path);
        return;
      }
      // ignore: mailto/지원불가 등 → 외부 이동 없이 무시.
    },
    [filePath, sourceKind, sourceId, openFile],
  );

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
      <div className="flex shrink-0 items-center gap-2.5 border-b border-border px-3 py-2">
        <span
          className="grid h-7 w-7 shrink-0 place-items-center rounded-lg"
          style={{ background: cfg.chipBg, color: cfg.chipFg }}
        >
          <Icon name={filePath ? "file" : cfg.icon} size={15} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12.5px] font-semibold leading-tight">{headerTitle}</p>
          <p className="truncate text-[11px] text-muted-foreground">{headerSub}</p>
        </div>
        {externalUrl ? (
          <a
            href={externalUrl}
            target="_blank"
            rel="noreferrer"
            className="interactive inline-flex items-center gap-1 rounded-full border border-border px-3 py-1 text-[11.5px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <Icon name="north_east" size={13} /> 열기
          </a>
        ) : null}
      </div>

      <div className="scroll-thin min-h-0 flex-1 overflow-y-auto">
        {/* 콘텐츠를 가로로 넓게 사용(좌우 여백만, 상한은 4xl). */}
        <div className="mx-auto w-full max-w-4xl px-5 py-5">
          {loading ? (
            <div className="grid place-items-center py-12 text-muted-foreground">
              <Icon name="progress_activity" size={22} className="animate-spin" />
            </div>
          ) : error ? (
            <p className="text-[13px] text-destructive">{error}</p>
          ) : (
            <Body
              source={source}
              content={content}
              filePath={filePath}
              onLinkClick={handleLinkClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}
