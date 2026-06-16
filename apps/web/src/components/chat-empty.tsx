"use client";

import { useSourceActions } from "../lib/source-actions";
import { Icon } from "./icon";

// 소스 0개일 때 가운데 채팅 자리를 채우는 온보딩 히어로.
// 빠른 시작 카드 3개는 공용 소스 추가 흐름(컨텍스트)을 그대로 호출한다.
interface QuickCard {
  icon: string;
  tint: string; // .studio-tint-* 키
  title: string;
  desc: string;
  action: "repo" | "file" | "url";
}

const CARDS: QuickCard[] = [
  {
    icon: "github",
    tint: "teal",
    title: "GitHub 저장소 연결",
    desc: "브랜치를 인덱싱해 코드 근거로 답합니다.",
    action: "repo",
  },
  {
    icon: "description",
    tint: "blue",
    title: "문서 · PDF 업로드",
    desc: "PDF · Markdown · 텍스트를 끌어다 놓거나 선택하세요.",
    action: "file",
  },
  {
    icon: "link",
    tint: "violet",
    title: "URL 추가",
    desc: "문서 페이지나 위키 링크를 소스로 등록합니다.",
    action: "url",
  },
];

export function ChatEmpty() {
  const { openFilePicker, openUrl, openRepo } = useSourceActions();
  const run = (action: QuickCard["action"]) => {
    if (action === "file") openFilePicker();
    else if (action === "url") openUrl();
    else openRepo();
  };

  return (
    <div className="scroll-thin flex-1 overflow-y-auto">
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-6 py-12">
        {/* 히어로: 큰 아이콘 + 헤드라인 + 설명 */}
        <span className="grid h-16 w-16 place-items-center rounded-3xl bg-accent text-accent-foreground shadow-elev-2">
          <Icon name="hub" size={32} />
        </span>
        <h1 className="mt-5 text-center text-[22px] font-semibold leading-tight tracking-tight">
          소스를 추가해 시작하세요
        </h1>
        <p className="mt-2.5 max-w-md text-center text-[13.5px] leading-relaxed text-muted-foreground">
          저장소·문서·링크를 연결하면 RepoLM이 근거 기반으로 답하고, 코드와 문서가 어긋난
          지점을 짚어냅니다.
        </p>

        {/* 빠른 시작 카드 3개 */}
        <div className="mt-8 grid w-full gap-3 sm:grid-cols-3">
          {CARDS.map((c) => (
            <button
              key={c.action}
              type="button"
              onClick={() => run(c.action)}
              className="interactive group flex flex-col items-start gap-3 rounded-2xl border border-border bg-card p-4 text-left hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-elev-2 active:scale-[0.99]"
            >
              <span
                className={`studio-tint studio-tint-${c.tint} grid h-11 w-11 place-items-center rounded-2xl`}
              >
                <Icon name={c.icon} size={20} />
              </span>
              <span className="w-full">
                <span className="flex items-center justify-between gap-1">
                  <span className="text-[14px] font-semibold leading-tight tracking-tight">
                    {c.title}
                  </span>
                  <Icon
                    name="north_east"
                    size={15}
                    className="shrink-0 text-muted-foreground/50 transition-colors group-hover:text-primary"
                  />
                </span>
                <span className="mt-1 block text-[12px] leading-relaxed text-muted-foreground">
                  {c.desc}
                </span>
              </span>
            </button>
          ))}
        </div>

        {/* 보조 안내: 드래그앤드롭 힌트 */}
        <p className="mt-7 flex items-center gap-1.5 text-[12px] text-muted-foreground">
          <Icon name="upload_file" size={14} />
          파일을 왼쪽 소스 패널로 끌어다 놓아도 됩니다.
        </p>
      </div>
    </div>
  );
}
