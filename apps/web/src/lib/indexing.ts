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

// 소스 단위 진행 라벨. 예: "인덱싱 중 3/8", "완료", "실패".
export function indexStatusLabel(progress: IndexProgress): string {
  switch (progress.status) {
    case "queued":
      return "대기 중";
    case "running":
      return progress.total_files > 0
        ? `인덱싱 중 ${progress.processed_files}/${progress.total_files}`
        : "인덱싱 중";
    case "done":
      return "완료";
    case "failed":
      return "실패";
  }
}

// 진행 중(아직 끝나지 않음) 여부.
export function isIndexActive(status: IndexStatus): boolean {
  return status === "queued" || status === "running";
}
