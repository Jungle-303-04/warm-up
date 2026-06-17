import type { GeneratableArtifactType, Source } from "./types";

function repoScopeLabel(source: Source): string {
  return `${source.title}${source.branch ? ` / ${source.branch}` : ""}`;
}

export function selectedSources(sources: Source[], sourceIds: Set<string>): Source[] {
  return sources.filter((source) => sourceIds.has(source.id));
}

export function artifactScopeWarning(
  type: GeneratableArtifactType,
  sources: Source[],
): string | null {
  if (type !== "uml" && type !== "erd") return null;
  const repoSources = sources.filter((source) => source.kind === "repo");
  if (repoSources.length <= 1) return null;

  const target = type === "uml" ? "UML 클래스 다이어그램" : "ERD";
  const options = repoSources
    .slice(0, 5)
    .map((source) => `- ${repoScopeLabel(source)}`)
    .join("\n");
  const suffix =
    repoSources.length > 5 ? `\n- 그 외 ${repoSources.length - 5}개 저장소` : "";

  return [
    `${target}은 저장소 하나를 기준으로 생성하는 편이 정확합니다.`,
    "현재 여러 저장소가 선택되어 있어요. 왼쪽 소스 패널에서 대상 저장소 하나만 선택한 뒤 다시 생성해 주세요.",
    options + suffix,
  ].join("\n");
}

export function buildGithubFileUrl(source: Source, path: string, startLine?: number | null): string | null {
  if (!source.repository_url || !source.repository_url.includes("github.com")) return null;
  const repoUrl = source.repository_url.replace(/\.git$/, "").replace(/\/$/, "");
  const branch = encodeURIComponent(source.branch || "main").replace(/%2F/g, "/");
  const encodedPath = path
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
  const lineHash = startLine ? `#L${startLine}` : "";
  return `${repoUrl}/blob/${branch}/${encodedPath}${lineHash}`;
}
