"use client";

import { useState } from "react";

import { deleteSource, getTree } from "../lib/api";
import { cn } from "../lib/cn";
import { SOURCE_KINDS } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { Source, TreeNode } from "../lib/types";
import { Icon } from "./icon";

// 재귀 파일 트리. 디렉터리는 펼침/접힘, 파일 클릭은 뷰어로 연다.
function TreeView({
  nodes,
  notebookId,
  sourceId,
  depth = 0,
}: {
  nodes: TreeNode[];
  notebookId: string;
  sourceId: string;
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
  depth,
}: {
  node: TreeNode;
  notebookId: string;
  sourceId: string;
  depth: number;
}) {
  const [open, setOpen] = useState(false);
  const openFile = useWorkspace((s) => s.openFile);
  const focused = useWorkspace(
    (s) => s.viewer?.sourceId === sourceId && s.viewer?.path === node.path,
  );
  const pad = { paddingLeft: `${depth * 12 + 8}px` };

  if (node.type === "dir") {
    return (
      <li>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          style={pad}
          className="flex w-full items-center gap-1 rounded-md py-1 pr-1 text-left text-[12px] transition-colors hover:bg-secondary"
        >
          <Icon
            name="chevron_right"
            size={13}
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
            depth={depth + 1}
          />
        ) : null}
      </li>
    );
  }

  return (
    <li>
      <button
        type="button"
        onClick={() => openFile(sourceId, node.path)}
        style={pad}
        className={cn(
          "flex w-full items-center gap-1 rounded-md py-1 pr-1 text-left text-[12px] transition-colors",
          focused ? "bg-secondary font-medium" : "hover:bg-secondary",
        )}
      >
        <span className="w-[13px] shrink-0" />
        <Icon name="file" size={13} className="shrink-0 text-muted-foreground" />
        <span className="truncate">{node.name}</span>
      </button>
    </li>
  );
}

// 한 행: 본문(뷰어 열기) + 삭제. 모든 소스는 자동으로 답변 범위에 포함된다(선택 없음).
// repo는 펼쳐 파일 트리 표시.
export function SourceRow({ source, notebookId }: { source: Source; notebookId: string }) {
  const focused = useWorkspace(
    (s) => s.viewer?.sourceId === source.id && !s.viewer?.path,
  );
  const openSource = useWorkspace((s) => s.openSource);
  const removeSource = useWorkspace((s) => s.removeSource);

  const [expanded, setExpanded] = useState(false);
  const [tree, setTree] = useState<TreeNode[] | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [treeError, setTreeError] = useState<string | null>(null);

  const cfg = SOURCE_KINDS[source.kind];
  const isRepo = source.kind === "repo";

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
      <div
        className={cn(
          "group flex items-center gap-1 rounded-lg pl-2 pr-1 transition-colors",
          focused ? "bg-secondary" : "hover:bg-secondary",
        )}
      >
        <button
          type="button"
          onClick={() => (isRepo ? toggleExpand() : openSource(source.id))}
          aria-current={focused ? "true" : undefined}
          title={isRepo ? `${source.title} 파일 트리` : `${source.title} 열기`}
          className="flex min-w-0 flex-1 items-center gap-2.5 rounded-lg py-1.5 pr-1 text-left"
        >
          <span
            className="grid h-7 w-7 shrink-0 place-items-center rounded-md"
            style={{ background: cfg.chipBg, color: cfg.chipFg }}
          >
            <Icon name={cfg.icon} size={16} />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-[13px] leading-tight">{source.title}</span>
            <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
              <span>{cfg.label}</span>
              {isRepo && source.branch ? (
                <>
                  <span aria-hidden>·</span>
                  <span className="truncate">{source.branch}</span>
                </>
              ) : null}
            </span>
          </span>
          {isRepo ? (
            <Icon
              name="chevron_right"
              size={15}
              className={cn(
                "shrink-0 text-muted-foreground transition-transform",
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
          className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
        >
          <Icon name="delete" size={15} />
        </button>
      </div>

      {isRepo && expanded ? (
        <div className="ml-9 mt-0.5 border-l border-border pl-1">
          {treeLoading ? (
            <p className="px-2 py-1 text-[11px] text-muted-foreground">불러오는 중…</p>
          ) : treeError ? (
            <p className="px-2 py-1 text-[11px] text-destructive">{treeError}</p>
          ) : tree && tree.length > 0 ? (
            <TreeView nodes={tree} notebookId={notebookId} sourceId={source.id} />
          ) : (
            <p className="px-2 py-1 text-[11px] text-muted-foreground">파일이 없습니다</p>
          )}
        </div>
      ) : null}
    </div>
  );
}
