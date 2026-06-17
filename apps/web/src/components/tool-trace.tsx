"use client";

import { useState } from "react";

import { Icon } from "./icon";

export interface ToolTraceStep {
  name: string;
  detail: string;
}

export function ToolTrace({ steps }: { steps: ToolTraceStep[] }) {
  const [open, setOpen] = useState(false);
  if (steps.length === 0) return null;

  return (
    <div className="mt-2 rounded-lg border border-border bg-secondary/40">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left text-[11px] font-semibold text-muted-foreground"
      >
        <Icon name="route" size={13} />
        도구 사용 {steps.length}단계
        <Icon
          name="chevron_right"
          size={13}
          className={`ml-auto transition-transform ${open ? "rotate-90" : ""}`}
        />
      </button>
      {open ? (
        <ol className="space-y-1 border-t border-border px-2.5 py-2">
          {steps.map((step, index) => (
            <li key={`${step.name}-${index}`} className="text-[11px] text-muted-foreground">
              <span className="font-semibold text-foreground">{step.name}</span>
              <span className="ml-1">{step.detail}</span>
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}
