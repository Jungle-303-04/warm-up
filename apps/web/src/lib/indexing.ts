// RAG 인덱싱 지원 판정 + 진행 표시용 공통 로직.
import type { IndexFile, IndexProgress, IndexStatus } from "./types";

// 백엔드가 인덱싱하는 확장자(트리에 SSE files 정보가 없을 때 보조 판정).
const SUPPORTED_EXTENSIONS = [".py", ".md", ".markdown"];

export function isSupportedPath(path: string): boolean {
  const lower = path.toLowerCase();
  return SUPPORTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

// 진행 스냅샷에서 경로별 파일 상태를 빠르게 찾기 위한 맵.
export function indexFilesByPath(progress?: IndexProgress): Map<string, IndexFile> {
  const map = new Map<string, IndexFile>();
  if (progress) for (const f of progress.files) map.set(f.path, f);
  return map;
}

// 진행 스냅샷에서 인덱싱 지원(supported) 파일 경로 목록.
// 파일 선택 기본값(전체 선택)·트라이스테이트 계산의 기준이 된다.
export function supportedFilePaths(progress?: IndexProgress): string[] {
  if (!progress) return [];
  return progress.files.filter((f) => f.supported).map((f) => f.path);
}

// 진행 중(아직 끝나지 않음) 여부.
export function isIndexActive(status: IndexStatus): boolean {
  return status === "queued" || status === "running";
}

// 답변 범위로 보낼 file_paths를 계산한다.
// - 범위 내 repo 소스 중 "부분 선택"(일부 supported 파일을 제외)이 하나도 없으면 null
//   → 백엔드는 파일 제한 없이 기존처럼 동작.
// - 부분 선택이 있으면, 범위 내 모든 repo 소스의 선택된 파일 경로 union을 보낸다.
//   (비repo 소스 청크는 file_path가 None이라 백엔드에서 항상 통과한다.)
export function scopeFilePaths(
  scopeRepoSourceIds: string[],
  indexProgress: Record<string, IndexProgress>,
  selectedFilePaths: Record<string, Set<string>>,
): string[] | null {
  let anyPartial = false;
  const union = new Set<string>();
  for (const sourceId of scopeRepoSourceIds) {
    const supported = supportedFilePaths(indexProgress[sourceId]);
    if (supported.length === 0) continue; // supported 목록을 모르면 제한하지 않는다.
    const selected = selectedFilePaths[sourceId];
    if (selected === undefined) {
      // 아직 초기화 전 → "전체 선택"으로 간주(부분 아님).
      for (const p of supported) union.add(p);
      continue;
    }
    const selectedSupported = supported.filter((p) => selected.has(p));
    if (selectedSupported.length < supported.length) anyPartial = true;
    for (const p of selectedSupported) union.add(p);
  }
  if (!anyPartial) return null;
  return [...union];
}
