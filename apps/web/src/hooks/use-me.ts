"use client";

import { useEffect, useState } from "react";

import { getMe, type Me } from "../lib/api";

// 현재 로그인한 GitHub 사용자. 데모 곳곳에서 "나/작성자" 식별에 쓴다.
export function useMe(): Me | null {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    getMe(controller.signal)
      .then(setMe)
      .catch(() => setMe(null));
    return () => controller.abort();
  }, []);
  return me;
}
