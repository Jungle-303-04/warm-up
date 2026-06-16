import { cn } from "../../lib/cn";
import { Icon } from "../icon";

// 아이콘 전용 원형 버튼. preparing=true면 비활성 + "준비 중" 툴팁(데드엔드 제거 일관화).
export function IconButton({
  name,
  label,
  size = 18,
  disabled = false,
  preparing = false,
  onClick,
  className,
}: {
  name: string;
  label: string;
  size?: number;
  disabled?: boolean;
  preparing?: boolean;
  onClick?: () => void;
  className?: string;
}) {
  const title = preparing ? `${label} · 준비 중` : label;
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      disabled={disabled || preparing}
      onClick={onClick}
      className={cn(
        "transition-all duration-200 ease-in-out grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent",
        className,
      )}
    >
      <Icon name={name} size={size} />
    </button>
  );
}
