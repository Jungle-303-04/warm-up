"use client";

import { useState } from "react";

import { useWorkspace } from "../lib/store";
import { Icon } from "./icon";
import { SourceAddModal } from "./source-add-modal";
import { Checkbox, SourceRow } from "./source-row";
import { IconButton } from "./ui/icon-button";
import { Panel } from "./ui/panel";

export function SourcesPanel({ notebookId }: { notebookId: string }) {
  const [addOpen, setAddOpen] = useState(false);
  const sources = useWorkspace((s) => s.sources);
  const selected = useWorkspace((s) => s.selected);
  const setAllSources = useWorkspace((s) => s.setAllSources);
  const allOn = sources.length > 0 && sources.every((s) => selected[s.id]);

  return (
    <Panel as="aside" className="w-[320px] shrink-0">
      <div className="flex items-center justify-between px-3 pt-3">
        <h2 className="text-[14px] font-semibold">소스</h2>
        <IconButton name="add" label="소스 추가" onClick={() => setAddOpen(true)} />
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-2 pt-1.5">
        {sources.length === 0 ? (
          <div className="mt-8 px-3 text-center">
            <span className="mx-auto grid h-10 w-10 place-items-center rounded-xl bg-secondary text-muted-foreground">
              <Icon name="description" size={20} />
            </span>
            <p className="mt-3 text-[13px] font-medium">소스가 없습니다</p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
              레포·문서·PDF·URL을 추가하면 답변 근거로 사용됩니다.
            </p>
            <button
              type="button"
              onClick={() => setAddOpen(true)}
              className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-[12px] transition-colors hover:bg-secondary"
            >
              <Icon name="add" size={16} /> 소스 추가
            </button>
          </div>
        ) : (
          <>
            <button
              type="button"
              aria-pressed={allOn}
              onClick={() => setAllSources(!allOn)}
              className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[12px] text-muted-foreground transition-colors hover:bg-secondary"
            >
              모든 소스 선택
              <Checkbox checked={allOn} />
            </button>
            <div className="mt-1 space-y-0.5">
              {sources.map((s) => (
                <SourceRow key={s.id} source={s} notebookId={notebookId} />
              ))}
            </div>
          </>
        )}
      </div>

      <SourceAddModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        notebookId={notebookId}
      />
    </Panel>
  );
}
