"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// 좌/우 패널 px 너비 상태. localStorage에 저장/복원하며 SSR 안전(초기값 → useEffect 로드).
const STORAGE_KEY = "repolm-panels";

// 클램프 경계(요구사항).
export const PANEL_LIMITS = {
  leftMin: 240,
  leftMax: 480,
  rightMin: 240,
  rightMax: 480,
  centerMin: 360,
} as const;

export interface PanelSizes {
  left: number;
  right: number;
}

const DEFAULTS: PanelSizes = { left: 320, right: 300 };

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

export function usePanelSizes() {
  // SSR-CSR 하이드레이션 불일치 방지: 항상 기본값으로 시작 후 마운트 시 복원.
  const [sizes, setSizes] = useState<PanelSizes>(DEFAULTS);
  const sizesRef = useRef(sizes);
  sizesRef.current = sizes;

  // 마운트 시 localStorage에서 복원.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<PanelSizes>;
      setSizes({
        left: clamp(parsed.left ?? DEFAULTS.left, PANEL_LIMITS.leftMin, PANEL_LIMITS.leftMax),
        right: clamp(parsed.right ?? DEFAULTS.right, PANEL_LIMITS.rightMin, PANEL_LIMITS.rightMax),
      });
    } catch {
      // 손상된 값은 무시하고 기본값 유지.
    }
  }, []);

  // 변경 시 저장.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sizes));
    } catch {
      // 저장 실패는 무시(프라이빗 모드 등).
    }
  }, [sizes]);

  // 좌 패널 너비 설정(가운데 최소폭 보장은 호출부 컨테이너 폭으로 계산).
  const setLeft = useCallback((next: number) => {
    setSizes((s) => ({ ...s, left: clamp(next, PANEL_LIMITS.leftMin, PANEL_LIMITS.leftMax) }));
  }, []);

  const setRight = useCallback((next: number) => {
    setSizes((s) => ({ ...s, right: clamp(next, PANEL_LIMITS.rightMin, PANEL_LIMITS.rightMax) }));
  }, []);

  return { sizes, setLeft, setRight, sizesRef };
}
