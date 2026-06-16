import { SourceIcon } from "./source-icon";

// 작고 촘촘한 출처 pill. 번호 배지 없이 파일 유형 아이콘 + 파일/링크명만 표시한다.
// URL 소스 인용은 favicon을 쓰고(로드 실패 시 link 폴백), 그 외는 정적 아이콘.
export function CitationChip({
  icon,
  label,
  url,
  isUrl = false,
  onClick,
}: {
  icon: string; // 파일 유형 아이콘(확장자/소스 종류 기반)
  label: string;
  url?: string | null; // URL 소스 인용일 때 favicon 추출용
  isUrl?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      title={label}
      onClick={onClick}
      className="interactive inline-flex max-w-full items-center gap-1 rounded-full border border-border bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground hover:border-primary/40 hover:text-foreground"
    >
      <SourceIcon
        iconName={icon}
        url={url}
        isUrl={isUrl}
        size={12}
        className="shrink-0 text-muted-foreground"
      />
      <span className="truncate font-mono">{label}</span>
    </button>
  );
}
