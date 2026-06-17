"use client";

import { fileIconForPath, SOURCE_KINDS } from "../lib/fixtures";
import { buildGithubFileUrl } from "../lib/source-scope";
import { useWorkspace } from "../lib/store";
import type { Citation } from "../lib/types";
import { CitationChip } from "./citation-chip";

function citationLabel(citation: Citation): string {
  if (citation.path) {
    const filename = citation.path.split("/").pop() || citation.path;
    const line = lineLabel(citation);
    return line ? `${filename}:${line}` : filename;
  }
  return citation.sourceName;
}

function lineLabel(citation: Citation): string | null {
  if (!citation.startLine) return null;
  if (citation.endLine && citation.endLine !== citation.startLine) {
    return `${citation.startLine}-${citation.endLine}`;
  }
  return String(citation.startLine);
}

function citationTitle(citation: Citation): string {
  const location = citation.path
    ? `${citation.sourceName} / ${citation.path}${lineLabel(citation) ? `:${lineLabel(citation)}` : ""}`
    : citation.sourceName;
  return citation.snippet ? `${location}\n\n${citation.snippet}` : location;
}

export function CitationList({ citations }: { citations: Citation[] }) {
  const openSource = useWorkspace((s) => s.openSource);
  const openFile = useWorkspace((s) => s.openFile);
  const sources = useWorkspace((s) => s.sources);
  const visibleCitations = dedupeCitationsByTarget(citations);

  return (
    <div className="flex flex-wrap gap-1 motion-safe:animate-[fadeIn_180ms_ease-out]">
      {visibleCitations.map((citation, index) => {
        const source = sources.find((s) => s.id === citation.sourceId);
        const icon = citation.path
          ? fileIconForPath(citation.path)
          : source
            ? SOURCE_KINDS[source.kind].icon
            : "link";
        const isUrl = !citation.path && source?.kind === "url";
        const href = citation.path && source
          ? buildGithubFileUrl(source, citation.path, citation.startLine)
          : isUrl
            ? source?.url
            : null;
        const open = () =>
          citation.path
            ? openFile(citation.sourceId, citation.path)
            : openSource(citation.sourceId);
        return (
          <CitationChip
            key={`${citation.sourceId}-${citation.path ?? "source"}-${index}`}
            icon={icon}
            label={citationLabel(citation)}
            title={citationTitle(citation)}
            url={isUrl ? source?.url : null}
            isUrl={isUrl}
            href={href}
            onClick={open}
          />
        );
      })}
    </div>
  );
}

function dedupeCitationsByTarget(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  const result: Citation[] = [];
  for (const citation of citations) {
    const key = citation.path
      ? `${citation.sourceId}:${citation.path}`
      : `${citation.sourceId}:__source__:${citation.snippet ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(citation);
  }
  return result;
}
