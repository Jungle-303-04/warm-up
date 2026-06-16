"use client";

import { useCallback, useEffect, useRef } from "react";

import { cn } from "../../lib/cn";

// 세로 드래그 핸들. 좌/우 패널 너비 조절용.
// - 마우스다운 → 문서 레벨 mousemove/mouseup 으로 누적 delta 를 onResize 로 전달.
// - 드래그 중 body 에 select-none + col-resize 커서 적용 후 해제.
// - 키보드: 좌우 화살표로 ±16px(onResize 호출).
export function ResizeHandle({
  ariaLabel,
  onResizeStart,
  onResize,
  className,
}: {
  ariaLabel: string;
  // 드래그 시작 시점에 기준 너비를 스냅샷하도록 호출부에 알린다.
  onResizeStart?: () => void;
  // delta(px): 시작점 대비 양수=오른쪽 이동. 호출부에서 어느 패널에 적용할지 결정.
  onResize: (deltaPx: number) => void;
  className?: string;
}) {
  const startXRef = useRef(0);
  const draggingRef = useRef(false);
  const onResizeRef = useRef(onResize);
  onResizeRef.current = onResize;
  const onResizeStartRef = useRef(onResizeStart);
  onResizeStartRef.current = onResizeStart;

  const handleMove = useCallback((e: MouseEvent) => {
    if (!draggingRef.current) return;
    onResizeRef.current(e.clientX - startXRef.current);
  }, []);

  const stop = useCallback(() => {
    draggingRef.current = false;
    document.removeEventListener("mousemove", handleMove);
    document.removeEventListener("mouseup", stop);
    // 드래그 중 적용한 전역 스타일 해제.
    document.body.classList.remove("select-none", "cursor-col-resize");
  }, [handleMove]);

  const startDrag = useCallback(
    (clientX: number) => {
      startXRef.current = clientX;
      draggingRef.current = true;
      onResizeStartRef.current?.();
      document.body.classList.add("select-none", "cursor-col-resize");
      document.addEventListener("mousemove", handleMove);
      document.addEventListener("mouseup", stop);
    },
    [handleMove, stop],
  );

  // 언마운트 시 리스너 정리.
  useEffect(() => stop, [stop]);

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={ariaLabel}
      tabIndex={0}
      onMouseDown={(e) => {
        e.preventDefault();
        startDrag(e.clientX);
      }}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          onResizeRef.current(-16);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          onResizeRef.current(16);
        }
      }}
      className={cn(
        // 가는 핸들 + 가로 패딩으로 hit area 확보. group 으로 내부 막대 하이라이트.
        "group relative hidden w-1.5 shrink-0 cursor-col-resize self-stretch md:flex",
        "items-center justify-center focus:outline-none",
        className,
      )}
    >
      {/* 시각 막대: hover/drag/focus 시 primary 톤 하이라이트. */}
      <span
        aria-hidden
        className="interactive h-10 w-full rounded-full bg-border group-hover:bg-primary/60 group-focus-visible:bg-primary group-active:bg-primary"
      />
    </div>
  );
}
