"use client";

import { useCallback, useEffect, useState } from "react";

import { cn } from "../lib/cn";

import { ARTIFACT_META, getArtifact, getFile, getSource, isMermaidArtifact } from "../lib/api";
import { isCodePath } from "../lib/file-kind";
import { fileIconForPath, SOURCE_KINDS } from "../lib/fixtures";
import { classifyLink } from "../lib/links";
import { useWorkspace } from "../lib/store";
import type { Artifact, Source } from "../lib/types";
import { CodeView } from "./code-view";
import { Icon } from "./icon";
import { MarkdownView } from "./markdown-view";
import { MermaidRender } from "./mermaid-render";
import { SourceIcon } from "./source-icon";
import { Button } from "./ui/button";

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
// 다수 사이트가 X-Frame-Options/CSP로 임베드를 막으므로 onError/타임아웃으로 폴백 안내를 표시
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
    // iframe 자체가 콘텐츠이므로 카드는 최소화: 상단에 얇은 배지 줄 + 본문은 평면 iframe.
    <div className="space-y-2.5">
      {/* URL/호스트/제목 배지 줄(카드 테두리 없이 한 줄로 단정하게) */}
      <div className="flex items-center gap-2">
        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-accent text-accent-foreground">
          <SourceIcon iconName="link" url={url} isUrl size={14} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12px] font-medium leading-tight">{source.title}</p>
          <p className="truncate text-[11px] text-muted-foreground">{host}</p>
        </div>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="interactive inline-flex h-7 shrink-0 items-center gap-1.5 rounded-full bg-primary px-3 text-[12px] font-medium text-primary-foreground hover:opacity-90"
        >
          <Icon name="north_east" size={13} /> 새 탭에서 열기
        </a>
      </div>

      {/* iframe 임베드 시도 + 차단 시 폴백 안내 */}
      {blocked ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border bg-secondary/40 px-4 py-8 text-center">
          <Icon name="public" size={22} className="text-muted-foreground" />
          <p className="text-[12px] font-medium">여기서 미리보기를 제공하지 않는 사이트입니다.</p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="interactive inline-flex h-7 items-center gap-1.5 rounded-full border border-border px-3 text-[12px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
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
          className="h-[70vh] w-full rounded-lg border border-border bg-card"
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

  // PDF 소스(파일 미선택): 추출 텍스트를 평면 문서형 뷰로 표시.
  // 카드 대신 상단에 작은 배지 줄만 두고, 본문은 패널에 직접 평면 렌더.
  if (source?.kind === "pdf" && !filePath) {
    return (
      <div>
        <div className="mb-3 flex items-center gap-2 border-b border-border pb-2.5">
          <span
            className={cn(
              "grid h-6 w-6 shrink-0 place-items-center rounded-md",
              "bg-[#FCEBEB] text-[#A32D2D]",
            )}
          >
            <Icon name="picture_as_pdf" size={14} />
          </span>
          <span className="text-[11px] font-medium text-muted-foreground">PDF · 추출 텍스트</span>
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
  // - repo-file: 현재 repo 소스이면 해석된 경로의 파일을 viewer로 열기 그 외 무시.
  const handleLinkClick = useCallback(
    (href: string) => {
      const resolved = classifyLink(href, filePath);
      if (resolved.type === "external") {
        // 외부 절대 URL(http/https, github blob 등) → 새 탭으로 실제 링크 열기.
        // noopener,noreferrer로 opener 탈취 방지. 앱 네비게이션은 발생하지 않음
        window.open(resolved.href, "_blank", "noopener,noreferrer");
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

  // 산출물 뷰어 대상이면 소스/파일 로딩을 건너뛴다(아래 ArtifactViewer가 담당).
  const artifactId = viewer?.artifactId;

  // viewer 대상이 바뀌면 내용을 로드한다(소스/파일 뷰어 전용).
  useEffect(() => {
    // 산출물 뷰어이거나 소스 식별자가 없으면 소스 로딩을 하지 않음
    if (!notebookId || artifactId || !sourceId) return;
    let active = true;
    setLoading(true);
    setError(null);
    setContent("");

    const load = filePath
      ? getFile(notebookId, sourceId, filePath).then((r) => r.content)
      : getSource(notebookId, sourceId).then((r) => r.content ?? "");

    load
      .then((c) => active && setContent(c))
      .catch((e) => active && setError(e instanceof Error ? e.message : "불러오기 실패"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [notebookId, artifactId, sourceId, filePath]);

  // 산출물 뷰어 대상이면 전용 컴포넌트로 렌더(Mermaid/마크다운 + 편집).
  if (artifactId) return <ArtifactViewer artifactId={artifactId} />;

  if (!viewer || !source) return <EmptyState />;

  const cfg = SOURCE_KINDS[source.kind];
  const headerTitle = filePath ?? source.title;
  const headerSub = filePath ? source.title : cfg.label;
  const externalUrl = source.url ?? source.repository_url ?? null;

  // 코드 뷰어/URL 프리뷰는 본문이 패널 폭을 직접 채우도록 좌우 패딩을 최소화함
  // 그 외(마크다운/텍스트/PDF)는 가독성을 위해 좌우 패딩만 둠
  const isCodeBody = isCodePath(filePath);
  const isUrlBody = source.kind === "url" && !filePath;
  const bodyPadding = isCodeBody ? "px-0 py-3" : isUrlBody ? "px-3 py-3" : "px-5 py-4";

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex shrink-0 items-center gap-2.5 border-b border-border px-3 py-2">
        <span
          className="grid h-7 w-7 shrink-0 place-items-center rounded-lg"
          style={{ background: cfg.chipBg, color: cfg.chipFg }}
        >
          {filePath ? (
            // 파일은 확장자별 또렷한 아이콘(py=코드, json=설정 등).
            <Icon name={fileIconForPath(filePath)} size={15} />
          ) : (
            <SourceIcon
              iconName={cfg.icon}
              url={source.url}
              isUrl={source.kind === "url"}
              size={15}
            />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12px] font-semibold leading-tight">{headerTitle}</p>
          <p className="truncate text-[11px] text-muted-foreground">{headerSub}</p>
        </div>
        {externalUrl ? (
          // 외부 열기 링크. 공용 sm/outline 알약과 동일한 크기·톤으로 통일.
          <a
            href={externalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-all duration-200 ease-in-out inline-flex h-7 shrink-0 items-center gap-1.5 rounded-full border border-border px-3 text-[12px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <Icon name="north_east" size={13} /> 열기
          </a>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {/* 본문을 패널 폭 전체로 사용(중앙 정렬·max-width 제거, 종류별 좌우 패딩만). */}
        <div className={cn("w-full", bodyPadding)}>
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

// ── 산출물(아티팩트/메모) 뷰어 ──────────────────────────────────────
// 가운데 패널에 산출물을 열어 보여주고 편집함
// - uml/erd/dependency: Mermaid 렌더 + 소스 편집(재렌더/저장)
// - change_summary/note: 마크다운 렌더 + 편집(저장)
function ArtifactViewer({ artifactId }: { artifactId: string }) {
  const notebookId = useWorkspace((s) => s.notebookId);
  const storeArtifacts = useWorkspace((s) => s.artifacts);
  const updateArtifact = useWorkspace((s) => s.updateArtifact);
  const addArtifactAsSource = useWorkspace((s) => s.addArtifactAsSource);

  const [artifact, setArtifact] = useState<Artifact | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 편집 중인 소스(content) 와 렌더에 반영된 소스(draft 와 분리해 "재렌더" 가능).
  const [draft, setDraft] = useState("");
  const [rendered, setRendered] = useState("");
  const [showEditor, setShowEditor] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  // 제목 인라인 편집 상태(편집 패널이 열려 있을 때만 입력 노출).
  const [titleDraft, setTitleDraft] = useState("");
  // 소스로 추가 진행/완료 표시.
  const [addingSource, setAddingSource] = useState(false);
  const [addedSource, setAddedSource] = useState(false);

  // 산출물 로드: 스토어 목록에 있으면 우선 사용하고, 없으면 단건 GET.
  useEffect(() => {
    if (!notebookId) return;
    const cached = storeArtifacts.find((a) => a.id === artifactId) ?? null;
    if (cached) {
      setArtifact(cached);
      setDraft(cached.content);
      setRendered(cached.content);
      setTitleDraft(cached.title);
      setError(null);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    getArtifact(notebookId, artifactId)
      .then((a) => {
        if (!active) return;
        setArtifact(a);
        setDraft(a.content);
        setRendered(a.content);
        setTitleDraft(a.title);
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : "산출물을 불러오지 못했습니다"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
    // storeArtifacts 변동 시 캐시 동기화는 별도 effect로 처리(여기선 id 기준 1회 로드).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notebookId, artifactId]);

  const isMermaid = artifact ? isMermaidArtifact(artifact.type) : false;
  const meta = artifact ? ARTIFACT_META[artifact.type] : null;

  const rerender = () => setRendered(draft);

  // 산출물 본문 링크: 절대 URL은 새 탭, 앵커는 페이지 내 스크롤, 그 외(상대 repo 경로 등)는
  // 매핑 대상이 없으므로 무시(산출물 뷰어엔 repo 컨텍스트가 없다).
  const handleArtifactLink = (href: string) => {
    const resolved = classifyLink(href, undefined);
    if (resolved.type === "external") {
      window.open(resolved.href, "_blank", "noopener,noreferrer");
    } else if (resolved.type === "anchor") {
      const id = decodeURIComponent(resolved.hash.slice(1));
      if (!id) return;
      const el =
        document.getElementById(id) ?? document.querySelector(`[name="${CSS.escape(id)}"]`);
      el?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    // repo-file/ignore: 무시.
  };

  const save = async () => {
    if (!artifact) return;
    setSaving(true);
    // 제목과 본문을 함께 저장(바뀐 항목만 PATCH).
    const patch: { title?: string; content?: string } = {};
    if (draft !== artifact.content) patch.content = draft;
    const nextTitle = titleDraft.trim();
    if (nextTitle && nextTitle !== artifact.title) patch.title = nextTitle;
    const updated = await updateArtifact(artifact.id, patch);
    setSaving(false);
    if (updated) {
      setArtifact(updated);
      setRendered(updated.content);
      setDraft(updated.content);
      setTitleDraft(updated.title);
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    }
  };

  // 산출물 content 로 새 소스를 만든다(좌측 소스 목록에 추가 + 자동 인덱싱).
  const addAsSource = async () => {
    if (!artifact) return;
    setAddingSource(true);
    const source = await addArtifactAsSource(artifact);
    setAddingSource(false);
    if (source) {
      setAddedSource(true);
      setTimeout(() => setAddedSource(false), 1800);
    }
  };

  if (loading) {
    return (
      <div className="grid flex-1 place-items-center text-muted-foreground">
        <Icon name="progress_activity" size={22} className="animate-spin" />
      </div>
    );
  }
  if (error || !artifact || !meta) {
    return (
      <div className="grid flex-1 place-items-center px-6 text-center text-muted-foreground">
        <p className="text-[13px] text-destructive">{error ?? "산출물을 찾을 수 없습니다."}</p>
      </div>
    );
  }

  // 제목 또는 본문이 바뀌었으면 저장 활성화.
  const dirty =
    draft !== artifact.content ||
    (titleDraft.trim() !== "" && titleDraft.trim() !== artifact.title);

  // 편집 패널(제목/본문 + 재렌더/저장). 다이어그램·마크다운 분기에서 공용으로 씀
  const editorPanel = showEditor ? (
    <div className="border-t border-border px-4 py-3">
      {/* 제목 편집(모든 산출물 공통). */}
      <label className="mb-1.5 block text-[11px] font-medium text-muted-foreground">제목</label>
      <input
        value={titleDraft}
        onChange={(e) => setTitleDraft(e.target.value)}
        placeholder="제목"
        className="mb-3 h-8 w-full rounded-lg border border-border bg-card px-3 text-[12.5px] font-medium text-foreground outline-none focus:border-primary/50"
      />
      <label className="mb-1.5 block text-[11px] font-medium text-muted-foreground">
        {isMermaid ? "Mermaid 소스" : "본문(Markdown)"}
      </label>
      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        spellCheck={false}
        className="h-40 w-full resize-y rounded-lg border border-border bg-card px-3 py-2 font-mono text-[12px] leading-relaxed text-foreground outline-none focus:border-primary/50"
      />
      <div className="mt-2 flex items-center justify-end gap-2">
        {isMermaid ? (
          <Button variant="outline" size="sm" icon="refresh" onClick={rerender} title="재렌더">
            재렌더
          </Button>
        ) : null}
        <Button
          variant="primary"
          size="sm"
          icon={saved ? "check" : "save_note"}
          loading={saving}
          onClick={() => void save()}
          disabled={saving || !dirty}
          title="저장"
        >
          {saving ? "저장 중…" : saved ? "저장됨" : "저장"}
        </Button>
      </div>
    </div>
  ) : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* 헤더: 아이콘·제목·종류 + 편집 토글 */}
      <div className="flex shrink-0 items-center gap-2.5 border-b border-border px-3 py-2">
        <span
          className={cn(
            "grid h-7 w-7 shrink-0 place-items-center rounded-lg",
            meta.tint === "grey"
              ? "bg-secondary text-muted-foreground"
              : `studio-tint studio-tint-${meta.tint}`,
          )}
        >
          <Icon name={meta.icon} size={15} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12px] font-semibold leading-tight">{artifact.title}</p>
          <p className="truncate text-[11px] text-muted-foreground">{meta.label}</p>
        </div>
        {/* 산출물 content 로 새 소스를 만든다(RAG 컨텍스트로 사용 가능). */}
        <Button
          variant="outline"
          size="sm"
          icon={addedSource ? "check" : "library_add"}
          loading={addingSource}
          onClick={() => void addAsSource()}
          disabled={addingSource}
          title="이 산출물을 소스로 추가"
        >
          {addingSource ? "추가 중…" : addedSource ? "추가됨" : "소스로 추가"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          icon="edit"
          onClick={() => setShowEditor((v) => !v)}
          title={showEditor ? "편집 닫기" : "소스 편집"}
          aria-pressed={showEditor}
          className={cn(showEditor && "border-primary/50 bg-primary/10 text-primary")}
        >
          편집
        </Button>
      </div>

      {/* 본문: Mermaid 다이어그램은 패널을 가로·세로로 꽉 채우고(카드 없음),
          마크다운(변경요약/메모)은 가독성 패딩과 함께 세로 스크롤로 표시한다. */}
      {isMermaid ? (
        <div className="flex min-h-0 flex-1 flex-col">
          {/* relative + 자식 absolute inset-0 으로 다이어그램이 영역을 꽉 채운다. */}
          <div className="relative min-h-0 flex-1">
            <MermaidRender source={rendered} />
          </div>
          {/* 편집 패널은 다이어그램 아래에 고정(자체 스크롤). */}
          {showEditor ? <div className="max-h-[45vh] shrink-0 overflow-y-auto">{editorPanel}</div> : null}
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <article className="markdown-body w-full px-5 py-4 text-[13.5px] leading-relaxed">
            {/* 산출물 마크다운(변경 요약/메모)의 절대 링크는 새 탭으로 실제 이동. */}
            <MarkdownView source={rendered} onLinkClick={handleArtifactLink} />
          </article>
          {editorPanel}
        </div>
      )}
    </div>
  );
}
