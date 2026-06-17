"use client";

import { useMemo } from "react";

import { scopeFilePaths } from "../lib/indexing";
import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";

export function SourceScopeBar() {
  const sources = useWorkspace((s) => s.sources);
  const selectedSourceIds = useWorkspace((s) => s.selectedSourceIds);
  const indexProgress = useWorkspace((s) => s.indexProgress);
  const selectedFilePaths = useWorkspace((s) => s.selectedFilePaths);

  const selected = useMemo(
    () => sources.filter((source) => selectedSourceIds.has(source.id)),
    [sources, selectedSourceIds],
  );
  const repoIds = selected.filter((source) => source.kind === "repo").map((source) => source.id);
  const scopedFiles = scopeFilePaths(repoIds, indexProgress, selectedFilePaths);

  if (sources.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 border-b border-border/70 px-4 py-2 text-[11px] text-muted-foreground">
      <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 font-semibold text-foreground/80">
        <Icon name="filter_alt" size={12} />
        소스 {selected.length}/{sources.length}
      </span>
      <span className="inline-flex items-center gap-1 rounded-md bg-secondary/70 px-1.5 py-0.5">
        <Icon name="description" size={12} />
        {scopedFiles === null ? "파일 전체" : `파일 ${scopedFiles.length}개`}
      </span>
      {selected.some((source) => source.derived_from_artifact_id) ? (
        <span className="inline-flex items-center gap-1 rounded-md bg-indigo-500/10 px-1.5 py-0.5 font-semibold text-indigo-600 dark:text-indigo-400">
          <Icon name="account_tree" size={12} />
          파생 소스 포함
        </span>
      ) : null}
    </div>
  );
}
