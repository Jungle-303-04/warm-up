import { SourceIcon } from "./source-icon";

// 작고 촘촘한 출처 pill. 번호 배지 없이 파일 유형 아이콘 + 파일/링크명만 표시
// URL 소스 인용은 favicon을 쓰고(로드 실패 시 link 폴백), 그 외는 정적 아이콘.
export function CitationChip({
  icon,
  label,
  title,
  url,
  isUrl = false,
  href,
  onClick,
}: {
  icon: string; // 파일 유형 아이콘(확장자/소스 종류 기반)
  label: string;
  title?: string;
  url?: string | null; // URL 소스 인용일 때 favicon 추출용
  isUrl?: boolean;
  href?: string | null; // 외부에서 열 수 있는 실제 URL(예: GitHub blob, URL 소스)
  onClick?: () => void;
}) {
  const className =
    "transition-all duration-200 ease-in-out inline-flex max-w-full items-center gap-1.5 rounded-lg border border-border bg-secondary/60 px-2.5 py-0.75 text-[11px] font-medium text-muted-foreground hover:border-primary/30 hover:bg-accent/60 hover:text-foreground shadow-sm";
  const content = (
    <>
      <SourceIcon
        iconName={icon}
        url={url}
        isUrl={isUrl}
        size={11.5}
        className="shrink-0 text-muted-foreground/85"
      />
      <span className="truncate font-sans tracking-tight">{label}</span>
    </>
  );

  if (href) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        title={title ?? label}
        className={className}
      >
        {content}
      </a>
    );
  }

  return (
    <button
      type="button"
      title={title ?? label}
      onClick={onClick}
      className={className}
    >
      {content}
    </button>
  );
}
