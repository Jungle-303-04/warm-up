"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "../lib/cn";
import { STUDIO_TILES, type StudioTile } from "../lib/fixtures";
import { selectScopeCount, useWorkspace } from "../lib/store";
import type { StudioArtifact } from "../lib/types";
import { Icon } from "./icon";
import { Panel } from "./ui/panel";

// 우 패널. 너비는 workspace 에서 style 로 주입(동적 리사이즈).
// 소스 0개면 생성 버튼만 비활성화하고 메모는 계속 만들 수 있게 둔다.
export function StudioPanel({
  style,
  onCollapse,
}: {
  style?: React.CSSProperties;
  onCollapse?: () => void;
}) {
  const sourceCount = useWorkspace((s) => s.sources.length);
  const scopeCount = useWorkspace(selectScopeCount);
  const artifacts = useWorkspace((s) => s.artifacts);
  const createArtifact = useWorkspace((s) => s.createArtifact);
  const addNote = useWorkspace((s) => s.addNote);
  const [status, setStatus] = useState<string | null>(null);
  // 생성 진입점을 하나로 통합한 메뉴 열림 상태.
  const [menuOpen, setMenuOpen] = useState(false);
  const canCreate = sourceCount > 0 && scopeCount > 0;

  const create = (tile: StudioTile) => {
    if (!canCreate) return;
    createArtifact({
      kind: "artifact",
      title: tile.label,
      typeLabel: tile.typeLabel,
      detail: `소스 ${scopeCount}개 · 방금 전`,
      icon: tile.icon,
      tint: tile.tint,
    });
    setStatus(`${tile.label} 생성됨`);
  };

  const createNote = () => {
    addNote();
    setStatus("새 메모 추가됨");
  };

  // 빈 산출물(메타 전용) 추가. 소스 범위가 있을 때만 의미가 있다.
  const createBlankArtifact = () => {
    createArtifact({
      kind: "artifact",
      title: "새 산출물",
      typeLabel: "산출물",
      detail: `소스 ${scopeCount}개 · 방금 전`,
      icon: "layers",
      tint: "blue",
    });
    setStatus("빈 산출물 추가됨");
  };

  return (
    <Panel as="aside" className="shrink-0" style={style}>
      <div className="flex h-11 items-center justify-between border-b border-border px-3">
        <div className="flex items-center gap-1.5">
          <Icon name="auto_awesome" size={15} className="text-primary" />
          <h2 className="t-title">스튜디오</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            소스 {scopeCount}개
          </span>
          {onCollapse ? (
            <button
              type="button"
              onClick={onCollapse}
              title="스튜디오 패널 접기"
              aria-label="스튜디오 패널 접기"
              className="interactive grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              <Icon name="dock_to_right" size={15} />
            </button>
          ) : null}
        </div>
      </div>

      <div className="scroll-thin relative flex-1 overflow-y-auto px-3 pb-3 pt-1">
        <div>
          {/* 기능 카드 그리드(히어로/안내 문구는 제거하고 카드만 남긴다). */}
          <div className="mt-2.5 grid grid-cols-2 gap-2">
            {STUDIO_TILES.map((t) => (
              <button
                key={t.label}
                type="button"
                disabled={!canCreate}
                onClick={() => create(t)}
                title={t.label}
                className="interactive group relative flex min-h-[104px] flex-col gap-2 rounded-xl border border-border bg-card p-3 text-left hover:-translate-y-0.5 hover:border-primary/35 hover:bg-surface-raised hover:shadow-elev-2 disabled:cursor-not-allowed disabled:opacity-55"
              >
                {t.beta ? (
                  <span className="absolute right-2 top-2 rounded-full bg-secondary px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-normal text-muted-foreground">
                    베타
                  </span>
                ) : null}
                <span
                  className={`studio-tint studio-tint-${t.tint} grid h-9 w-9 place-items-center rounded-lg`}
                >
                  <Icon name={t.icon} size={18} />
                </span>
                <span className="min-w-0">
                  <span className="flex items-center justify-between gap-1">
                    <span className="truncate text-[13px] font-semibold leading-tight">
                      {t.label}
                    </span>
                    <Icon
                      name="chevron_right"
                      size={14}
                      className="shrink-0 text-muted-foreground/40 transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                    />
                  </span>
                  <span className="mt-0.5 block text-[11px] leading-snug text-muted-foreground">
                    {t.hint}
                  </span>
                </span>
              </button>
            ))}
          </div>

          {status ? (
            <p className="mt-2.5 rounded-lg bg-accent/70 px-3 py-1.5 text-[11.5px] font-medium text-accent-foreground">
              {status}
            </p>
          ) : null}

          <div className="mt-5 flex items-center justify-between border-t border-border pt-3.5">
            <p className="t-section">아티팩트 및 메모</p>
            {/* 생성 진입점을 하나로 통합한 메뉴(+ 추가). */}
            <CreateMenu
              open={menuOpen}
              setOpen={setMenuOpen}
              canCreate={canCreate}
              onAddNote={createNote}
              onAddArtifact={createBlankArtifact}
            />
          </div>

          <div className="mt-2 space-y-1">
            {artifacts.length > 0 ? (
              artifacts.map((artifact) => <ArtifactItem key={artifact.id} artifact={artifact} />)
            ) : (
              // 빈 상태일 때만 단일 생성 안내(점선 중복 버튼 제거).
              <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-border px-3 py-5 text-center">
                <p className="text-[12px] text-muted-foreground">아직 항목이 없습니다.</p>
                <button
                  type="button"
                  onClick={createNote}
                  title="메모 추가"
                  className="interactive inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
                >
                  <Icon name="note_add" size={12} /> 메모 추가
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Panel>
  );
}

// 생성 진입점 통합 메뉴. 헤더의 "+ 추가" 클릭 시 메모/빈 산출물 선택지를 연다.
function CreateMenu({
  open,
  setOpen,
  canCreate,
  onAddNote,
  onAddArtifact,
}: {
  open: boolean;
  setOpen: (v: boolean) => void;
  canCreate: boolean;
  onAddNote: () => void;
  onAddArtifact: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  // 바깥 클릭 시 메뉴 닫기.
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open, setOpen]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        title="추가"
        aria-haspopup="menu"
        aria-expanded={open}
        className="interactive inline-flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
      >
        <Icon name="add" size={12} /> 추가
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-full z-10 mt-1 w-40 overflow-hidden rounded-lg border border-border bg-card py-1 shadow-elev-2"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              onAddNote();
              setOpen(false);
            }}
            className="interactive flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px] text-foreground hover:bg-secondary"
          >
            <Icon name="note_add" size={14} className="text-muted-foreground" /> 메모 추가
          </button>
          <button
            type="button"
            role="menuitem"
            disabled={!canCreate}
            onClick={() => {
              if (!canCreate) return;
              onAddArtifact();
              setOpen(false);
            }}
            className="interactive flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px] text-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Icon name="layers" size={14} className="text-muted-foreground" /> 빈 산출물 추가
          </button>
        </div>
      ) : null}
    </div>
  );
}

// 콤팩트 항목 행. 높이·패딩·아이콘·폰트를 줄여 한 줄에 가깝게 표시.
// hover 시 우측에 휴지통(삭제) 노출.
function ArtifactItem({ artifact }: { artifact: StudioArtifact }) {
  const removeArtifact = useWorkspace((s) => s.removeArtifact);
  return (
    <div
      title={artifact.title}
      className="interactive group flex w-full items-center gap-2 rounded-lg border border-border bg-card px-2.5 py-1.5 text-left hover:border-primary/30 hover:shadow-elev-1"
    >
      <span
        className={cn(
          "grid h-6 w-6 shrink-0 place-items-center rounded-md",
          artifact.tint === "grey"
            ? "bg-secondary text-muted-foreground"
            : `studio-tint studio-tint-${artifact.tint}`,
        )}
      >
        <Icon name={artifact.icon} size={13} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12px] font-medium leading-tight">
          {artifact.title}
        </span>
        <span className="mt-px flex items-center gap-1 text-[10.5px] text-muted-foreground">
          <span className="truncate">{artifact.typeLabel}</span>
          <span aria-hidden>·</span>
          <span className="truncate">{artifact.detail}</span>
        </span>
      </span>
      <button
        type="button"
        onClick={() => removeArtifact(artifact.id)}
        title="삭제"
        aria-label={`${artifact.title} 삭제`}
        className="interactive grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted-foreground/60 opacity-0 transition-opacity hover:bg-secondary hover:text-destructive group-hover:opacity-100"
      >
        <Icon name="delete" size={13} />
      </button>
    </div>
  );
}
