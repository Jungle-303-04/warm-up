"use client";

import { useEffect, useState } from "react";

import { Icon } from "./icon";

type Pref = "system" | "light" | "dark";

const ORDER: Pref[] = ["system", "light", "dark"];
const ICON: Record<Pref, string> = {
  system: "brightness_auto",
  light: "light_mode",
  dark: "dark_mode",
};

export function ThemeToggle() {
  const [pref, setPref] = useState<Pref>("system");

  useEffect(() => {
    setPref((localStorage.getItem("repolm-theme") as Pref) || "system");
  }, []);

  function apply(next: Pref) {
    localStorage.setItem("repolm-theme", next);
    const dark =
      next === "dark" ||
      (next === "system" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);
    const root = document.documentElement;
    root.classList.toggle("dark", dark);
    root.classList.toggle("light", !dark);
    setPref(next);
  }

  return (
    <button
      type="button"
      title={`테마: ${pref}`}
      onClick={() => apply(ORDER[(ORDER.indexOf(pref) + 1) % ORDER.length])}
      className="grid h-8 w-8 place-items-center rounded-md text-muted transition-colors hover:bg-elev hover:text-ink"
    >
      <Icon name={ICON[pref]} className="text-[20px]" />
    </button>
  );
}
