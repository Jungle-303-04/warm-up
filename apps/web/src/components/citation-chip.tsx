export function CitationChip({ index, label }: { index: number; label: string }) {
  return (
    <button
      type="button"
      title={label}
      className="interactive inline-flex max-w-full items-center gap-1.5 rounded-full border border-border bg-secondary py-1 pl-1 pr-2.5 text-[11.5px] text-muted-foreground hover:border-primary/40 hover:text-foreground"
    >
      <span className="grid h-4 w-4 shrink-0 place-items-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
        {index}
      </span>
      <span className="truncate font-mono">{label}</span>
    </button>
  );
}
