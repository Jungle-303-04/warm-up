"use client";

import { useEffect, useState } from "react";

import { IconButton } from "./ui/icon-button";

type Mode = "light" | "dark";

// 현재 모드 기준, 누르면 갈 방향을 안내(라이트면 달=다크로, 다크면 해=라이트로).
const ICON: Record<Mode, string> = { light: "dark_mode", dark: "light_mode" };
const LABEL: Record<Mode, string> = { light: "다크로", dark: "라이트로" };

function apply(mode: Mode) {
  const el = document.documentElement;
  el.classList.toggle("dark", mode === "dark");
  el.classList.toggle("light", mode === "light");
}

// 라이트↔다크 토글(기본 라이트). localStorage("repolm-theme")에 저장.
export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>("light");

  useEffect(() => {
    setMode(localStorage.getItem("repolm-theme") === "dark" ? "dark" : "light");
  }, []);

  const toggle = () => {
    const next: Mode = mode === "light" ? "dark" : "light";
    setMode(next);
    localStorage.setItem("repolm-theme", next);
    apply(next);
  };

  return <IconButton name={ICON[mode]} label={`테마: ${LABEL[mode]}`} onClick={toggle} />;
}
