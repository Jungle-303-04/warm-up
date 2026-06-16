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
      className="transition-all duration-200 ease-in-out inline-flex max-w-full items-center gap-1.5 rounded-lg border border-border bg-secondary/60 px-2.5 py-0.75 text-[11px] font-medium text-muted-foreground hover:border-primary/30 hover:bg-accent/60 hover:text-foreground shadow-sm"
    >
      <SourceIcon
        iconName={icon}
        url={url}
        isUrl={isUrl}
        size={11.5}
        className="shrink-0 text-muted-foreground/85"
      />
      <span className="truncate font-sans tracking-tight">{label}</span>
    </button>
  );
}
