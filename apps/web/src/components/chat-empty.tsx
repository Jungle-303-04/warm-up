"use client";

import { useSourceActions } from "../lib/source-actions";
import { Icon } from "./icon";

// 소스 0개일 때 가운데 채팅 자리를 채우는 온보딩 히어로.
// 빠른 시작 카드 3개는 공용 소스 추가 흐름(컨텍스트)을 그대로 호출함
interface QuickCard {
  icon: string;
  tintCls: string; // Tailwind bg & text 클래스
  title: string;
  desc: string;
}

// 빠른 시작 카드 3개 모두 단일 통합 소스 추가 모달을 연다(진입점 일원화).
const CARDS: QuickCard[] = [
  {
    icon: "github",
    tintCls: "bg-teal-500/10 text-teal-600 dark:bg-teal-500/20 dark:text-teal-400",
    title: "GitHub 저장소 연결",
    desc: "URL을 붙여넣으면 브랜치를 인식해 코드 근거로 답합니다.",
  },
  {
    icon: "description",
    tintCls: "bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400",
    title: "문서 · PDF 업로드",
    desc: "PDF · Markdown · 텍스트를 끌어다 놓거나 선택하세요.",
  },
  {
    icon: "link",
    tintCls: "bg-violet-500/10 text-violet-600 dark:bg-violet-500/20 dark:text-violet-400",
    title: "링크 추가",
    desc: "문서 페이지·위키 링크나 GitHub 주소를 소스로 등록합니다.",
  },
];

export function ChatEmpty() {
  const { openAddSource } = useSourceActions();

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col items-center justify-center px-6 py-10">
        {/* 히어로: 큰 아이콘 + 헤드라인 + 설명 */}
        <span className="grid h-14 w-14 place-items-center rounded-3xl bg-accent text-accent-foreground shadow">
          <Icon name="hub" size={28} />
        </span>
        <h1 className="mt-4 text-center text-[19px] font-semibold leading-tight">
          소스를 추가해 시작하세요
        </h1>
        <p className="mt-2 max-w-md text-center text-[13px] leading-relaxed text-muted-foreground">
          저장소·문서·링크를 연결하면 RepoLM이 근거 기반으로 답하고, 코드와 문서가 어긋난
          지점을 짚어냅니다.
        </p>

        {/* 빠른 시작 카드 3개 */}
        <div className="mt-6 grid w-full gap-2.5 sm:grid-cols-3">
          {CARDS.map((c) => (
            <button
              key={c.title}
              type="button"
              onClick={openAddSource}
              className="transition-all duration-200 ease-in-out group flex flex-col items-start gap-2.5 rounded-2xl border border-border bg-card p-3.5 text-left hover:-translate-y-0.5 hover:border-primary/40 hover:shadow active:scale-[0.99]"
            >
              <span
                className={`${c.tintCls} grid h-10 w-10 place-items-center rounded-2xl`}
              >
                <Icon name={c.icon} size={18} />
              </span>
              <span className="w-full">
                <span className="flex items-center justify-between gap-1">
                  <span className="text-[13px] font-semibold leading-tight">
                    {c.title}
                  </span>
                  <Icon
                    name="north_east"
                    size={14}
                    className="shrink-0 text-muted-foreground/50 transition-colors group-hover:text-primary"
                  />
                </span>
                <span className="mt-1 block text-[11.5px] leading-relaxed text-muted-foreground">
                  {c.desc}
                </span>
              </span>
            </button>
          ))}
        </div>

        {/* 보조 안내: 드래그앤드롭 힌트 */}
        <p className="mt-6 flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
          <Icon name="upload_file" size={13} />
          파일을 왼쪽 소스 패널로 끌어다 놓아도 됩니다.
        </p>
      </div>
    </div>
  );
}
