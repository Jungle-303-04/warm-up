"use client";

import { useMemo, useState } from "react";

import { BOARD_STATUS_META, BOARD_STATUS_ORDER, TODAY } from "../lib/fixtures";
import { useWorkspace } from "../lib/store";
import type { BoardStatus, BoardTask, BoardView } from "../lib/types";
import { Icon } from "./icon";

// ── 날짜 유틸 (외부 라이브러리 없이) ────────────────────────────────
const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const addDays = (d: Date, n: number) => {
  const x = startOfDay(d);
  x.setDate(x.getDate() + n);
  return x;
};
const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() &&
  a.getMonth() === b.getMonth() &&
  a.getDate() === b.getDate();
const isoDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
const parseISO = (s: string) => {
  const [y, m, day] = s.split("-").map(Number);
  return new Date(y, m - 1, day);
};
// 월요일 시작 주
const startOfWeek = (d: Date) => addDays(d, -((d.getDay() + 6) % 7));

const WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"];
const VIEWS: { id: BoardView; label: string; icon: string }[] = [
  { id: "kanban", label: "칸반", icon: "schema" },
  { id: "week", label: "주", icon: "calendar_month" },
  { id: "calendar", label: "캘린더", icon: "calendar_month" },
  { id: "list", label: "목록", icon: "checklist" },
];

function groupByDate(tasks: BoardTask[]) {
  const map = new Map<string, BoardTask[]>();
  for (const t of tasks) {
    const list = map.get(t.due) ?? [];
    list.push(t);
    map.set(t.due, list);
  }
  return map;
}

function StatusDot({ status }: { status: BoardStatus }) {
  return (
    <span
      className="inline-block h-2 w-2 shrink-0 rounded-full"
      style={{ background: BOARD_STATUS_META[status].dotFg }}
      aria-hidden
    />
  );
}

function TaskCard({ task }: { task: BoardTask }) {
  const due = parseISO(task.due);
  return (
    <div className="rounded-lg border border-border bg-card px-2.5 py-2 shadow-sm">
      <p className="text-[12px] font-medium leading-snug">{task.title}</p>
      <div className="mt-1 flex items-center gap-1.5 text-[10px] text-muted-foreground">
        <StatusDot status={task.status} />
        <span className="truncate">{task.repo}</span>
        <span aria-hidden>·</span>
        <span>
          {due.getMonth() + 1}/{due.getDate()}
        </span>
      </div>
    </div>
  );
}

function ViewSwitcher({
  view,
  onChange,
}: {
  view: BoardView;
  onChange: (v: BoardView) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-secondary/40 p-0.5">
      {VIEWS.map((v) => (
        <button
          key={v.id}
          type="button"
          aria-pressed={view === v.id}
          onClick={() => onChange(v.id)}
          className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-[12px] transition-colors ${
            view === v.id
              ? "bg-card font-semibold text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Icon name={v.icon} size={14} />
          {v.label}
        </button>
      ))}
    </div>
  );
}

function NavHeader({
  label,
  onPrev,
  onNext,
  onToday,
}: {
  label: string;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={onToday}
        className="rounded-md border border-border px-2 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        오늘
      </button>
      <button
        type="button"
        aria-label="이전"
        onClick={onPrev}
        className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <Icon name="chevron_right" size={16} className="rotate-180" />
      </button>
      <span className="min-w-[88px] text-center text-[13px] font-semibold">{label}</span>
      <button
        type="button"
        aria-label="다음"
        onClick={onNext}
        className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <Icon name="chevron_right" size={16} />
      </button>
    </div>
  );
}

function KanbanView({ tasks }: { tasks: BoardTask[] }) {
  return (
    <div className="grid h-full grid-cols-3 gap-3">
      {BOARD_STATUS_ORDER.map((status) => {
        const items = tasks.filter((t) => t.status === status);
        return (
          <div key={status} className="flex min-h-0 flex-col rounded-xl bg-secondary/30 p-2">
            <div className="flex items-center gap-1.5 px-1 pb-2 text-[12px] font-semibold">
              <StatusDot status={status} />
              {BOARD_STATUS_META[status].label}
              <span className="text-muted-foreground">{items.length}</span>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto">
              {items.map((t) => (
                <TaskCard key={t.id} task={t} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function WeekView({ cursor, tasks }: { cursor: Date; tasks: BoardTask[] }) {
  const start = startOfWeek(cursor);
  const days = Array.from({ length: 7 }, (_, i) => addDays(start, i));
  const byDate = useMemo(() => groupByDate(tasks), [tasks]);
  return (
    <div className="grid h-full grid-cols-7 gap-2">
      {days.map((d, i) => {
        const items = byDate.get(isoDate(d)) ?? [];
        const today = sameDay(d, TODAY);
        return (
          <div key={isoDate(d)} className="flex min-h-0 flex-col rounded-xl bg-secondary/30 p-1.5">
            <div className="px-1 pb-1.5 text-[11px]">
              <span className="text-muted-foreground">{WEEKDAYS[i]}</span>{" "}
              <span
                className={
                  today
                    ? "inline-grid h-5 w-5 place-items-center rounded-full bg-primary text-primary-foreground"
                    : "font-semibold"
                }
              >
                {d.getDate()}
              </span>
            </div>
            <div className="flex-1 space-y-1.5 overflow-y-auto">
              {items.map((t) => (
                <TaskCard key={t.id} task={t} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CalendarView({ cursor, tasks }: { cursor: Date; tasks: BoardTask[] }) {
  const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const gridStart = startOfWeek(first);
  const cells = Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
  const byDate = useMemo(() => groupByDate(tasks), [tasks]);
  return (
    <div className="flex h-full flex-col">
      <div className="grid grid-cols-7 border-b border-border pb-1">
        {WEEKDAYS.map((w) => (
          <div key={w} className="text-center text-[11px] font-medium text-muted-foreground">
            {w}
          </div>
        ))}
      </div>
      <div className="grid flex-1 grid-cols-7 grid-rows-6">
        {cells.map((d) => {
          const items = byDate.get(isoDate(d)) ?? [];
          const inMonth = d.getMonth() === cursor.getMonth();
          const today = sameDay(d, TODAY);
          return (
            <div
              key={isoDate(d)}
              className="min-h-0 border-b border-r border-border p-1 last:border-r-0"
            >
              <div className="mb-1 text-[11px]">
                <span
                  className={
                    today
                      ? "inline-grid h-5 w-5 place-items-center rounded-full bg-primary text-primary-foreground"
                      : inMonth
                        ? "text-foreground"
                        : "text-muted-foreground/50"
                  }
                >
                  {d.getDate()}
                </span>
              </div>
              <div className="space-y-1">
                {items.slice(0, 2).map((t) => (
                  <div
                    key={t.id}
                    title={`${t.title} · ${t.repo}`}
                    className="flex items-center gap-1 rounded bg-secondary px-1 py-0.5 text-[10px]"
                  >
                    <StatusDot status={t.status} />
                    <span className="truncate">{t.title}</span>
                  </div>
                ))}
                {items.length > 2 ? (
                  <div className="px-1 text-[10px] text-muted-foreground">
                    +{items.length - 2}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ListView({ tasks }: { tasks: BoardTask[] }) {
  return (
    <div className="space-y-4">
      {BOARD_STATUS_ORDER.map((status) => {
        const items = tasks
          .filter((t) => t.status === status)
          .sort((a, b) => a.due.localeCompare(b.due));
        return (
          <div key={status}>
            <div className="mb-1.5 flex items-center gap-1.5 text-[12px] font-semibold">
              <StatusDot status={status} />
              {BOARD_STATUS_META[status].label}
              <span className="text-muted-foreground">{items.length}</span>
            </div>
            <div className="overflow-hidden rounded-xl border border-border">
              {items.map((t, i) => {
                const due = parseISO(t.due);
                return (
                  <div
                    key={t.id}
                    className={`flex items-center gap-3 px-3 py-2 text-[13px] ${
                      i > 0 ? "border-t border-border" : ""
                    }`}
                  >
                    <span className="flex-1 truncate">{t.title}</span>
                    <span className="shrink-0 text-[11px] text-muted-foreground">{t.repo}</span>
                    <span className="shrink-0 text-[11px] text-muted-foreground">
                      {due.getMonth() + 1}/{due.getDate()}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function BoardPanel() {
  const tasks = useWorkspace((s) => s.boardTasks);
  const [view, setView] = useState<BoardView>("kanban");
  const [cursor, setCursor] = useState<Date>(TODAY);

  const navLabel =
    view === "week"
      ? (() => {
          const s = startOfWeek(cursor);
          const e = addDays(s, 6);
          return `${s.getMonth() + 1}/${s.getDate()} – ${e.getMonth() + 1}/${e.getDate()}`;
        })()
      : `${cursor.getFullYear()}년 ${cursor.getMonth() + 1}월`;

  const step = (dir: number) => {
    if (view === "week") setCursor((c) => addDays(c, dir * 7));
    else setCursor((c) => new Date(c.getFullYear(), c.getMonth() + dir, 1));
  };

  const showNav = view === "week" || view === "calendar";

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <ViewSwitcher view={view} onChange={setView} />
        {showNav ? (
          <NavHeader
            label={navLabel}
            onPrev={() => step(-1)}
            onNext={() => step(1)}
            onToday={() => setCursor(TODAY)}
          />
        ) : null}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {view === "kanban" ? (
          <KanbanView tasks={tasks} />
        ) : view === "week" ? (
          <WeekView cursor={cursor} tasks={tasks} />
        ) : view === "calendar" ? (
          <CalendarView cursor={cursor} tasks={tasks} />
        ) : (
          <ListView tasks={tasks} />
        )}
      </div>
    </div>
  );
}
