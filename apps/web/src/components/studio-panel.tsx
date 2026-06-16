"use client";

import { useState } from "react";

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
  const empty = sourceCount === 0;
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
        {!canCreate ? (
          <div className="mb-2.5 mt-2.5 flex items-start gap-2 rounded-lg border border-dashed border-border bg-secondary/40 px-3 py-2 text-[11.5px] leading-snug text-muted-foreground">
            <Icon name={empty ? "check_circle" : "label_auto"} size={13} className="mt-0.5 shrink-0" />
            <span>{empty ? "소스를 추가하면 스튜디오 산출물을 만들 수 있어요." : "선택된 소스가 있어야 산출물을 만들 수 있어요."}</span>
          </div>
        ) : null}

        <div>
          <div className="mt-2.5 rounded-lg border border-border bg-surface-raised px-3 py-2.5">
            <p className="t-section flex items-center gap-2">
              <Icon name="layers" size={14} className="text-primary" />
              코드 이해 산출물
            </p>
            <p className="mt-1 text-[11.5px] leading-relaxed text-muted-foreground">
              선택한 소스만 기준으로 구조, 데이터 관계, 의존성, 변경 흐름을 정리합니다.
            </p>
          </div>

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
            <button
              type="button"
              onClick={createNote}
              title="메모 추가"
              className="interactive inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[11.5px] font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              <Icon name="add" size={14} /> 추가
            </button>
          </div>

          <div className="mt-2 space-y-1.5">
            {artifacts.length > 0 ? (
              artifacts.map((artifact) => <ArtifactItem key={artifact.id} artifact={artifact} />)
            ) : (
              <div className="rounded-xl border border-dashed border-border px-3 py-4 text-center text-[12px] text-muted-foreground">
                아직 생성된 항목이 없습니다.
              </div>
            )}

            <button
              type="button"
              onClick={createNote}
              title="메모 추가"
              className="interactive flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-border px-3 py-2 text-[12px] text-muted-foreground hover:bg-secondary"
            >
              <Icon name="note_add" size={15} /> 새 메모
            </button>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function ArtifactItem({ artifact }: { artifact: StudioArtifact }) {
  return (
    <button
      type="button"
      title={artifact.title}
      className="interactive flex w-full items-center gap-2.5 rounded-xl border border-border bg-card px-3 py-2 text-left hover:border-primary/30 hover:shadow-elev-1"
    >
      <span
        className={cn(
          "grid h-8 w-8 shrink-0 place-items-center rounded-lg",
          artifact.tint === "grey"
            ? "bg-secondary text-muted-foreground"
            : `studio-tint studio-tint-${artifact.tint}`,
        )}
      >
        <Icon name={artifact.icon} size={16} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[12.5px] font-semibold leading-tight">
          {artifact.title}
        </span>
        <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
          <span className="truncate">{artifact.typeLabel}</span>
          <span aria-hidden>·</span>
          <span className="truncate">{artifact.detail}</span>
        </span>
      </span>
      <Icon name="more_vert" size={15} className="shrink-0 text-muted-foreground/60" />
    </button>
  );
}
