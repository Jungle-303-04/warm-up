"use client";

import { useState } from "react";

import { useIndexProgress } from "../hooks/use-index-progress";
import { deleteSource, getTree } from "../lib/api";
import { cn } from "../lib/cn";
import { SOURCE_KINDS } from "../lib/fixtures";
import {
  indexFilesByPath,
  indexStatusLabel,
  isIndexActive,
  isSupportedPath,
} from "../lib/indexing";
import { useWorkspace } from "../lib/store";
import type { IndexFile, IndexProgress, Source, TreeNode } from "../lib/types";
import { Icon } from "./icon";
import { ProgressBar } from "./ui/progress-bar";

// 파일 단위 인덱싱 상태 → 아이콘/색.
function fileStatusIcon(status: IndexFile["status"]): { icon: string; spin: boolean; className: string } {
  switch (status) {
    case "done":
      return { icon: "check_circle", spin: false, className: "text-primary" };
    case "indexing":
      return { icon: "progress_activity", spin: true, className: "text-primary" };
    case "failed":
      return { icon: "report", spin: false, className: "text-destructive" };
    case "skipped":
      return { icon: "remove", spin: false, className: "text-muted-foreground/60" };
    case "queued":
      return { icon: "schedule", spin: false, className: "text-muted-foreground" };
  }
}

// 재귀 파일 트리. 디렉터리는 펼침/접힘, 파일 클릭은 뷰어로 연다.
function TreeView({
  nodes,
  notebookId,
  sourceId,
  filesByPath,
  depth = 0,
}: {
  nodes: TreeNode[];
  notebookId: string;
  sourceId: string;
  filesByPath: Map<string, IndexFile>;
  depth?: number;
}) {
  return (
    <ul>
      {nodes.map((node) => (
        <TreeItem
          key={node.path}
          node={node}
          notebookId={notebookId}
          sourceId={sourceId}
          filesByPath={filesByPath}
          depth={depth}
        />
      ))}
    </ul>
  );
}

function TreeItem({
  node,
  notebookId,
  sourceId,
  filesByPath,
  depth,
}: {
  node: TreeNode;
  notebookId: string;
  sourceId: string;
  filesByPath: Map<string, IndexFile>;
  depth: number;
}) {
  const [open, setOpen] = useState(false);
  const openFile = useWorkspace((s) => s.openFile);
  const focused = useWorkspace(
    (s) => s.viewer?.sourceId === sourceId && s.viewer?.path === node.path,
  );
  const pad = { paddingLeft: `${depth * 11 + 6}px` };

  if (node.type === "dir") {
    return (
      <li>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          style={pad}
          className="interactive flex w-full items-center gap-1.5 rounded-md py-1 pr-2 text-left text-[12px] hover:bg-secondary"
        >
          <Icon
            name="chevron_right"
            size={12}
            className={cn("shrink-0 text-muted-foreground transition-transform", open && "rotate-90")}
          />
          <Icon name="folder" size={13} className="shrink-0 text-muted-foreground" />
          <span className="truncate">{node.name}</span>
        </button>
        {open && node.children ? (
          <TreeView
            nodes={node.children}
            notebookId={notebookId}
            sourceId={sourceId}
            filesByPath={filesByPath}
            depth={depth + 1}
          />
        ) : null}
      </li>
    );
  }

  // supported 판정: SSE files[].supported 우선, 없으면 확장자 보조 판정.
  const indexed = filesByPath.get(node.path);
  const supported = indexed ? indexed.supported : isSupportedPath(node.path);
  const status = indexed?.status;

  return (
    <li>
      <button
        type="button"
        onClick={() => openFile(sourceId, node.path)}
        style={pad}
        title={supported ? node.path : `${node.path} · 인덱싱 미지원`}
        className={cn(
          "interactive flex w-full items-center gap-1.5 rounded-md py-1 pr-2 text-left text-[12px]",
          focused
            ? "bg-accent font-medium text-accent-foreground"
            : "hover:bg-secondary",
          !supported && !focused && "text-muted-foreground/70",
        )}
      >
        <span className="w-[12px] shrink-0" />
        <Icon
          name="file"
          size={13}
          className={cn(
            "shrink-0",
            focused
              ? "text-accent-foreground"
              : supported
                ? "text-muted-foreground"
                : "text-muted-foreground/45",
          )}
        />
        <span className="truncate">{node.name}</span>
        {supported && status ? (
          <FileStatusBadge status={status} />
        ) : !supported ? (
          <span className="ml-auto shrink-0 rounded-full bg-secondary px-1.5 py-px text-[9px] font-medium text-muted-foreground/70">
            미지원
          </span>
        ) : null}
      </button>
    </li>
  );
}

function FileStatusBadge({ status }: { status: IndexFile["status"] }) {
  const { icon, spin, className } = fileStatusIcon(status);
  return (
    <Icon
      name={icon}
      size={12}
      className={cn("ml-auto shrink-0", className, spin && "animate-spin")}
    />
  );
}

// 소스 단위 인덱싱 진행 표시(얇은 진행바 + %/상태).
function IndexProgressRow({ progress }: { progress: IndexProgress }) {
  const failed = progress.status === "failed";
  const done = progress.status === "done";
  const active = isIndexActive(progress.status);

  return (
    <div className="px-2 py-1.5 text-[11px] text-muted-foreground">
      <p className="flex items-center gap-1.5">
        <Icon
          name={failed ? "report" : done ? "check_circle" : "progress_activity"}
          size={12}
          className={cn(
            active && "animate-spin",
            failed ? "text-destructive" : done ? "text-primary" : undefined,
          )}
        />
        <span className="font-medium text-foreground">{indexStatusLabel(progress)}</span>
        <span className="ml-auto tabular-nums">{Math.round(progress.percent)}%</span>
      </p>
      <ProgressBar
        percent={progress.percent}
        tone={failed ? "danger" : done ? "success" : "primary"}
        className="mt-1"
      />
      {failed && progress.error ? (
        <p className="mt-1 line-clamp-2 text-[10px] text-destructive">{progress.error}</p>
      ) : done ? (
        <p className="mt-1 text-[10px]">
          청크 {progress.indexed_chunks}개 인덱싱 · 미지원 {progress.skipped_files}개 제외
        </p>
      ) : null}
    </div>
  );
}

// 한 행: 본문(뷰어 열기) + 삭제. 모든 소스는 자동으로 답변 범위에 포함된다(선택 없음).
// repo는 펼쳐 파일 트리 표시. 마운트되는 동안 인덱싱 진행을 SSE로 구독한다.
export function SourceRow({ source, notebookId }: { source: Source; notebookId: string }) {
  // 진행 구독(언마운트/완료 시 내부에서 EventSource close).
  useIndexProgress(notebookId, source.id);

  const focused = useWorkspace((s) => s.viewer?.sourceId === source.id && !s.viewer?.path);
  const openSource = useWorkspace((s) => s.openSource);
  const removeSource = useWorkspace((s) => s.removeSource);
  const selected = useWorkspace((s) => s.selectedSourceIds.has(source.id));
  const toggleSelected = useWorkspace((s) => s.toggleSourceSelected);
  const progress = useWorkspace((s) => s.indexProgress[source.id]);

  const [expanded, setExpanded] = useState(false);
  const [tree, setTree] = useState<TreeNode[] | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [treeError, setTreeError] = useState<string | null>(null);

  const cfg = SOURCE_KINDS[source.kind];
  const isRepo = source.kind === "repo";
  const filesByPath = indexFilesByPath(progress);

  const toggleExpand = async () => {
    const next = !expanded;
    setExpanded(next);
    // 처음 펼칠 때 트리 로드.
    if (next && tree === null && !treeLoading) {
      setTreeLoading(true);
      setTreeError(null);
      try {
        const res = await getTree(notebookId, source.id);
        setTree(res.tree);
      } catch (e) {
        setTreeError(e instanceof Error ? e.message : "트리 로드 실패");
      } finally {
        setTreeLoading(false);
      }
    }
  };

  const handleDelete = async () => {
    try {
      await deleteSource(notebookId, source.id);
      removeSource(source.id);
    } catch {
      // 삭제 실패는 무시(낙관적 미적용). 필요 시 토스트로 확장.
    }
  };

  return (
    <div>
      {/* 한 줄: 체크박스 · kind 아이콘 · 제목(truncate) · (repo) chevron · hover 삭제 */}
      <div
        className={cn(
          "group interactive flex items-center gap-1 rounded-lg pl-1.5 pr-1",
          focused ? "bg-accent" : "hover:bg-secondary",
          !selected && "opacity-65",
        )}
      >
        <label
          className="interactive grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-card/70"
          title={selected ? "소스 범위에서 제외" : "소스 범위에 포함"}
          onClick={(e) => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={selected}
            onChange={() => toggleSelected(source.id)}
            aria-label={`${source.title} 선택`}
            className="peer sr-only"
          />
          <span
            aria-hidden
            className={cn(
              "grid h-4 w-4 place-items-center rounded-[4px] border border-input bg-card",
              selected && "border-primary bg-primary text-primary-foreground",
            )}
          >
            {selected ? <Icon name="check" size={12} strokeWidth={2.5} /> : null}
          </span>
        </label>
        <button
          type="button"
          onClick={() => (isRepo ? toggleExpand() : openSource(source.id))}
          aria-current={focused ? "true" : undefined}
          title={isRepo ? `${cfg.label} · ${source.title} 파일 트리` : `${cfg.label} · ${source.title}`}
          className="flex min-w-0 flex-1 items-center gap-2 rounded-lg py-1.5 pr-1 text-left"
        >
          <span
            className="grid h-6 w-6 shrink-0 place-items-center rounded-md"
            style={{ background: cfg.chipBg, color: cfg.chipFg }}
          >
            <Icon name={cfg.icon} size={14} />
          </span>
          <span
            className={cn(
              "min-w-0 flex-1 truncate text-[12.5px] font-medium leading-tight",
              focused && "text-accent-foreground",
            )}
          >
            {source.title}
            {isRepo && source.branch ? (
              <span
                className={cn(
                  "ml-1 font-normal",
                  focused ? "text-accent-foreground/60" : "text-muted-foreground/60",
                )}
              >
                {source.branch}
              </span>
            ) : null}
          </span>
          {isRepo ? (
            <Icon
              name="chevron_right"
              size={15}
              className={cn(
                "shrink-0 transition-transform",
                focused ? "text-accent-foreground" : "text-muted-foreground",
                expanded && "rotate-90",
              )}
            />
          ) : null}
        </button>

        <button
          type="button"
          onClick={handleDelete}
          aria-label={`${source.title} 삭제`}
          title="소스 삭제"
          className="interactive grid h-7 w-7 shrink-0 place-items-center rounded-md text-muted-foreground opacity-0 hover:bg-destructive/10 hover:text-destructive focus-visible:opacity-100 group-hover:opacity-100"
        >
          <Icon name="delete" size={14} />
        </button>
      </div>

      {/* 진행 표시는 repo가 아니어도 인덱싱 중이면 노출(md/text/pdf 포함). */}
      <div className={cn(isRepo && "ml-[15px] mt-0.5 border-l border-border pl-1.5")}>
        {progress ? <IndexProgressRow progress={progress} /> : null}

        {isRepo && expanded ? (
          treeLoading ? (
            <p className="flex items-center gap-1.5 px-2 py-1 text-[11px] text-muted-foreground">
              <Icon name="progress_activity" size={12} className="animate-spin" />
              불러오는 중…
            </p>
          ) : treeError ? (
            <p className="px-2 py-1 text-[11px] text-destructive">{treeError}</p>
          ) : tree && tree.length > 0 ? (
            <TreeView
              nodes={tree}
              notebookId={notebookId}
              sourceId={source.id}
              filesByPath={filesByPath}
            />
          ) : (
            <p className="px-2 py-1 text-[11px] text-muted-foreground">파일이 없습니다</p>
          )
        ) : null}
      </div>
    </div>
  );
}
