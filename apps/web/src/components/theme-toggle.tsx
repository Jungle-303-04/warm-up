"use client";

import { useEffect, useState } from "react";

import { IconButton } from "./ui/icon-button";

type Mode = "system" | "light" | "dark";

const ICON: Record<Mode, string> = {
  system: "theme_system",
  light: "light_mode",
  dark: "dark_mode",
};
const NEXT: Record<Mode, Mode> = { system: "light", light: "dark", dark: "system" };
const LABEL: Record<Mode, string> = { system: "시스템", light: "라이트", dark: "다크" };

function apply(mode: Mode) {
  const dark =
    mode === "dark" ||
    (mode === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const el = document.documentElement;
  el.classList.toggle("dark", dark);
  el.classList.toggle("light", !dark);
}

// 시스템→라이트→다크 순환(기본 시스템). localStorage("repolm-theme")에 저장.
export function ThemeToggle() {
  const [mode, setMode] = useState<Mode>("system");

  useEffect(() => {
    setMode((localStorage.getItem("repolm-theme") as Mode) || "system");
  }, []);

  const cycle = () => {
    const next = NEXT[mode];
    setMode(next);
    localStorage.setItem("repolm-theme", next);
    apply(next);
  };

  return <IconButton name={ICON[mode]} label={`테마: ${LABEL[mode]}`} onClick={cycle} />;
}
