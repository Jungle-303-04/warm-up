"use client";

import type { Source } from "../lib/types";
import { Icon } from "./icon";

export function ArtifactLineageBadge({ source }: { source: Source }) {
  if (!source.derived_from_artifact_id) return null;
  const count = source.lineage_source_ids?.length ?? 0;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400"
      title={`artifact ${source.derived_from_artifact_id}`}
    >
      <Icon name="account_tree" size={11} />
      파생{count > 0 ? ` ${count}` : ""}
    </span>
  );
}
