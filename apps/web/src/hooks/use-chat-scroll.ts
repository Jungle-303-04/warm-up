"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// 채팅 자동 스크롤. 하단 근처면 새 메시지/타이핑마다 바닥으로 고정하고,
// 사용자가 위로 스크롤하면 고정을 멈춘다. deps가 바뀔 때마다 재평가.
const STICK_THRESHOLD_PX = 80; // 이 거리 이내면 "하단 고정" 상태로 본다.

export function useChatScroll(deps: unknown[]) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [stick, setStick] = useState(true);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStick(distance <= STICK_THRESHOLD_PX);
  }, []);

  useEffect(() => {
    if (!stick) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
    // deps: 메시지 수/타이핑 텍스트 변화에 반응.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { scrollRef, onScroll };
}
