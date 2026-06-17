"use client";

import { fileIconForPath, SOURCE_KINDS } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { Citation } from "../lib/types";
import { CitationChip } from "./citation-chip";

function citationLabel(citation: Citation): string {
  if (citation.path) return citation.path.split("/").pop() || citation.path;
  return citation.sourceName;
}

export function CitationList({ citations }: { citations: Citation[] }) {
  const openSource = useWorkspace((s) => s.openSource);
  const openFile = useWorkspace((s) => s.openFile);
  const sources = useWorkspace((s) => s.sources);

  return (
    <div className="flex flex-wrap gap-1 motion-safe:animate-[fadeIn_180ms_ease-out]">
      {citations.map((citation, index) => {
        const source = sources.find((s) => s.id === citation.sourceId);
        const icon = citation.path
          ? fileIconForPath(citation.path)
          : source
            ? SOURCE_KINDS[source.kind].icon
            : "link";
        const isUrl = !citation.path && source?.kind === "url";
        const open = () =>
          citation.path
            ? openFile(citation.sourceId, citation.path)
            : openSource(citation.sourceId);
        return (
          <CitationChip
            key={`${citation.sourceId}-${citation.path ?? "source"}-${index}`}
            icon={icon}
            label={citationLabel(citation)}
            url={isUrl ? source?.url : null}
            isUrl={isUrl}
            onClick={open}
          />
        );
      })}
    </div>
  );
}
