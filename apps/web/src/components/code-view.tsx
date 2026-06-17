"use client";

import { useEffect, useMemo, useState } from "react";

import { languageOfPath } from "../lib/file-kind";

// 줄 수 계산(마지막 빈 줄은 거터 번호에서 제외).
function countLines(text: string): number {
  const normalized = text.replace(/\r\n?/g, "\n");
  const lines = normalized.split("\n");
  if (lines.length > 1 && lines[lines.length - 1] === "") lines.pop();
  return Math.max(1, lines.length);
}

// GitHub풍 코드 뷰어: 좌측 줄 번호 거터 + highlight.js 구문 강조.
// 하이라이트는 동적 import로 분리해 초기 번들 영향을 최소화한다.
// 거터와 코드는 동일한 line-height를 가진 별도 컬럼으로, 줄 단위 HTML 분할 없이
// 강조 결과 전체를 하나의 <pre>로 렌더한다(다줄 토큰의 HTML 깨짐 방지).
export function CodeView({ content, filePath }: { content: string; filePath?: string }) {
  const lineCount = useMemo(() => countLines(content), [content]);
  // highlight.js 강조 HTML. 로드 전/실패 시 null → 평문 폴백.
  const [highlightedHtml, setHighlightedHtml] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setHighlightedHtml(null);
    // 동적 import로 highlight.js 코어를 지연 로드.
    import("highlight.js/lib/common")
      .then((mod) => {
        if (!active) return;
        const hljs = mod.default;
        const lang = languageOfPath(filePath);
        try {
          const result =
            lang && hljs.getLanguage(lang)
              ? hljs.highlight(content, { language: lang, ignoreIllegals: true })
              : hljs.highlightAuto(content);
          setHighlightedHtml(result.value);
        } catch {
          if (active) setHighlightedHtml(null);
        }
      })
      .catch(() => {
        if (active) setHighlightedHtml(null);
      });
    return () => {
      active = false;
    };
  }, [content, filePath]);

  // 거터 폭: 자리수에 맞춰 가변. 최소 2자리.
  const gutterDigits = Math.max(2, String(lineCount).length);

  return (
    // 외곽 카드/테두리 없이 패널에 직접 평면 렌더(줄번호 거터 + 코드만, 패널 폭 전체 사용).
    <div className="flex overflow-x-auto">
      {/* 줄 번호 거터: user-select:none으로 복사 시 번호 제외. sticky로 가로 스크롤 시 고정. */}
      <pre
        aria-hidden
        className="sticky left-0 shrink-0 select-none border-r border-border bg-card pr-3 text-right font-mono text-[12.5px] leading-[1.6] text-muted-foreground/70"
        style={{ minWidth: `calc(${gutterDigits}ch + 0.75rem)` }}
      >
        {Array.from({ length: lineCount }, (_, i) => i + 1).join("\n")}
      </pre>
      {/* 코드 본문: 강조 HTML 전체를 한 번에 렌더. 가로 스크롤·고정폭 폰트. */}
      <pre className="hljs w-full min-w-0 bg-transparent pl-4 pr-4 font-mono text-[12.5px] leading-[1.6]">
        {highlightedHtml !== null ? (
          <code
            // highlight.js 토큰 span. 색은 globals.css의 .hljs-* 스코프가 담당.
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        ) : (
          <code>{content}</code>
        )}
      </pre>
    </div>
  );
}
