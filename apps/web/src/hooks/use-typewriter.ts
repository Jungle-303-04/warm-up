"use client";

import { useEffect, useRef, useState } from "react";

// 한 글자/청크씩 텍스트를 출력하는 타이핑 효과.
// enabled=false면 즉시 전체를 보여준다(기록 복원/접근성용).
// 반환: 현재까지 출력된 텍스트, 진행 여부, 즉시 완료(stop).
const CHARS_PER_TICK = 3; // 틱당 출력 글자 수(체감 속도).
const TICK_MS = 16; // 약 60fps.

export function useTypewriter(
  full: string,
  enabled: boolean,
): { text: string; done: boolean; stop: () => void } {
  const [count, setCount] = useState(enabled ? 0 : full.length);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clear = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    if (!enabled) {
      setCount(full.length);
      return;
    }
    setCount(0);
    timerRef.current = setInterval(() => {
      setCount((prev) => {
        const next = prev + CHARS_PER_TICK;
        if (next >= full.length) {
          clear();
          return full.length;
        }
        return next;
      });
    }, TICK_MS);
    return clear;
  }, [full, enabled]);

  const stop = () => {
    clear();
    setCount(full.length);
  };

  return { text: full.slice(0, count), done: count >= full.length, stop };
}
