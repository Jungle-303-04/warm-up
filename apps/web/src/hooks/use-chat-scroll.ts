"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// 채팅 자동 스크롤. 하단 근처면 새 메시지/타이핑마다 바닥으로 고정하고,
// 사용자가 위로 스크롤하면 고정을 멈춘다.
// - deps(메시지 수/대기 상태) 변화에 반응.
// - 타이핑으로 콘텐츠 높이가 늘어나는 동안에도 하단으로 따라가도록
//   스크롤 영역 자체의 크기 변화를 ResizeObserver로 감지한다.
const STICK_THRESHOLD_PX = 80; // 이 거리 이내면 "하단 고정" 상태로 본다.

export function useChatScroll(deps: unknown[]) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [stick, setStick] = useState(true);
  // 최신 stick 값을 옵저버 콜백에서 참조하기 위한 ref(리바인딩 회피).
  const stickRef = useRef(stick);
  stickRef.current = stick;

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStick(distance <= STICK_THRESHOLD_PX);
  }, []);

  const scrollToBottom = () => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  // deps(메시지 수/타이핑 텍스트 변화에 반응) 변화 시 하단 고정.
  useEffect(() => {
    if (!stick) return;
    scrollToBottom();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  // 콘텐츠 높이 변화(타이핑으로 메시지가 길어지는 등)에도 하단 고정.
  // 사용자가 위로 스크롤(stick=false)했으면 따라가지 않는다.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      if (stickRef.current) scrollToBottom();
    });
    // 스크롤 컨테이너의 내용(첫 자식)을 관찰해 높이 증가를 감지.
    const target = el.firstElementChild ?? el;
    observer.observe(target);
    return () => observer.disconnect();
  }, []);

  return { scrollRef, onScroll };
}
