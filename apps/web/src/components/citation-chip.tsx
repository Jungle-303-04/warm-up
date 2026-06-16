export function CitationChip({
  index,
  label,
  onClick,
}: {
  index: number;
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      title={label}
      onClick={onClick}
      className="interactive inline-flex max-w-full items-center gap-1.5 rounded-full border border-border bg-secondary py-0.5 pl-0.5 pr-2.5 text-[11px] text-muted-foreground hover:border-primary/40 hover:text-foreground"
    >
      <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
        {index}
      </span>
      <span className="truncate font-mono">{label}</span>
    </button>
  );
}
