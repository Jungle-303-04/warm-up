export function CitationChip({ index, label }: { index: number; label: string }) {
  return (
    <button
      type="button"
      title={label}
      className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[11px] text-muted-foreground transition-colors hover:text-foreground"
    >
      <span className="grid h-4 w-4 place-items-center rounded bg-primary/10 text-[10px] font-medium text-primary">
        {index}
      </span>
      {label}
    </button>
  );
}
