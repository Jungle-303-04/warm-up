import { cn } from "../../lib/cn";

// 공통 얇은 진행바. percent는 0~100으로 클램프된다.
// tone=primary(진행), success(완료), danger(실패).
export function ProgressBar({
  percent,
  tone = "primary",
  className,
}: {
  percent: number;
  tone?: "primary" | "success" | "danger";
  className?: string;
}) {
  const clamped = Math.min(100, Math.max(0, percent));
  const fill =
    tone === "danger"
      ? "bg-destructive/80"
      : tone === "success"
        ? "bg-primary"
        : "bg-primary/85";
  return (
    <div className={cn("h-1.5 w-full overflow-hidden rounded-full bg-secondary", className)}>
      <div
        className={cn("h-full rounded-full transition-all duration-300", fill)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
