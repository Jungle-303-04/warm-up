import { Icon } from "./icon";

// 작고 촘촘한 출처 pill. 번호 배지 없이 파일 유형 아이콘 + 파일/링크명만 표시한다.
export function CitationChip({
  icon,
  label,
  onClick,
}: {
  icon: string; // 파일 유형 아이콘(확장자/소스 종류 기반)
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      title={label}
      onClick={onClick}
      className="interactive inline-flex max-w-full items-center gap-1 rounded-full border border-border bg-secondary px-2 py-0.5 text-[10.5px] text-muted-foreground hover:border-primary/40 hover:text-foreground"
    >
      <Icon name={icon} size={11} className="shrink-0 text-muted-foreground" />
      <span className="truncate font-mono">{label}</span>
    </button>
  );
}
