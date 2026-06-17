"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// 채팅 자동 스크롤. 하단 근처면 새 메시지/타이핑마다 바닥으로 고정하고,
// 사용자가 위로 스크롤하면 고정을 중지
// - deps(메시지 수/대기 상태) 변화에 반응.
// - 타이핑으로 콘텐츠 높이가 늘어나는 동안에도 하단으로 따라가도록
//   스크롤 영역 자체의 크기 변화를 ResizeObserver + MutationObserver로 감지함
const STICK_THRESHOLD_PX = 120; // 이 거리 이내면 "하단 고정" 상태로 본다.

export function useChatScroll(deps: unknown[]) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [stick, setStick] = useState(true);
  // 최신 stick 값을 옵저버 콜백에서 참조하기 위한 ref(리바인딩 회피).
  const stickRef = useRef(stick);
  stickRef.current = stick;

  // 프로그래밍 스크롤 중에는 onScroll에서 stick을 false로 바꾸지 않도록 가드.
  const programmaticRef = useRef(false);

  const onScroll = useCallback(() => {
    if (programmaticRef.current) return;
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setStick(distance <= STICK_THRESHOLD_PX);
  }, []);

  const scrollToBottom = useCallback((smooth = false) => {
    const el = scrollRef.current;
    if (!el) return;
    programmaticRef.current = true;
    if (smooth) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      // smooth 스크롤은 비동기이므로 약간 뒤에 가드 해제.
      setTimeout(() => { programmaticRef.current = false; }, 400);
    } else {
      el.scrollTop = el.scrollHeight;
      // 즉시 해제 대신 한 프레임 뒤에 해제(scroll 이벤트 레이싱 방지).
      requestAnimationFrame(() => { programmaticRef.current = false; });
    }
  }, []);

  // deps(메시지 수/타이핑 텍스트 변화에 반응) 변화 시 하단 고정.
  useEffect(() => {
    if (!stick) return;
    // smooth: 새 메시지가 도착할 때 자연스럽게 슬라이드.
    scrollToBottom(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  // 콘텐츠 높이 변화(타이핑으로 메시지가 길어지는 등)에도 하단 고정.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const scrollIfStuck = () => {
      if (stickRef.current) {
        el.scrollTop = el.scrollHeight;
      }
    };

    // ResizeObserver: 내부 콘텐츠 크기 변화 감지.
    let resizeObs: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      resizeObs = new ResizeObserver(scrollIfStuck);
      const target = el.firstElementChild ?? el;
      resizeObs.observe(target);
    }

    // MutationObserver: DOM 노드 추가(새 메시지 엘리먼트 삽입) 감지.
    const mutObs = new MutationObserver(scrollIfStuck);
    mutObs.observe(el, { childList: true, subtree: true });

    return () => {
      resizeObs?.disconnect();
      mutObs.disconnect();
    };
  }, []);

  return { scrollRef, onScroll, scrollToBottom };
}

