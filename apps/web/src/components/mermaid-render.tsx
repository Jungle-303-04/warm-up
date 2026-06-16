"use client";

import { useEffect, useId, useRef, useState } from "react";

// 현재 문서 테마(.dark 클래스)에 따라 mermaid 테마를 고른다.
function isDarkTheme(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.classList.contains("dark");
}

// Mermaid 다이어그램을 동적 import 로 렌더한다(SSR 안전).
// 렌더 실패 시 onError 로 에러를 위임해 호출부가 원본 소스를 노출하게 한다.
export function MermaidRender({
  source,
  onError,
}: {
  source: string;
  // 렌더 성공/실패를 호출부에 알린다(null = 성공).
  onError?: (message: string | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const reactId = useId();
  // mermaid id 는 CSS 식별자라야 하므로 콜론을 제거한다.
  const renderId = `mmd-${reactId.replace(/[^a-zA-Z0-9_-]/g, "")}`;
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  // 테마가 바뀌면 재렌더하도록 토글 카운터를 둔다.
  const [themeTick, setThemeTick] = useState(0);

  // .dark 클래스 변동을 관찰해 테마 전환 시 다이어그램을 다시 그린다.
  useEffect(() => {
    const el = document.documentElement;
    const observer = new MutationObserver(() => setThemeTick((n) => n + 1));
    observer.observe(el, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;
    const trimmed = source.trim();
    if (!trimmed) {
      setSvg("");
      setError(null);
      onError?.(null);
      return;
    }

    (async () => {
      try {
        // 동적 import: 클라이언트에서만 mermaid 를 로드한다.
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: isDarkTheme() ? "dark" : "default",
          fontFamily: "var(--font-sans, Pretendard, sans-serif)",
        });
        // parse 로 문법을 먼저 검증(에러 메시지 품질↑).
        await mermaid.parse(trimmed);
        const { svg: rendered } = await mermaid.render(renderId, trimmed);
        if (!active) return;
        setSvg(rendered);
        setError(null);
        onError?.(null);
      } catch (e) {
        if (!active) return;
        const message = e instanceof Error ? e.message : "다이어그램을 렌더링하지 못했습니다";
        setSvg("");
        setError(message);
        onError?.(message);
      }
    })();

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, themeTick, renderId]);

  if (error) {
    return (
      <div className="space-y-2">
        {/* 렌더 실패 시 에러 메시지 + 원본 Mermaid 소스를 함께 노출(편집/디버깅용). */}
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2.5 text-[12.5px] text-destructive">
          <p className="font-medium">다이어그램 렌더 실패</p>
          <p className="mt-1 whitespace-pre-wrap break-words text-[11.5px] opacity-90">{error}</p>
        </div>
        <pre className="scroll-thin max-h-72 overflow-auto rounded-lg border border-border bg-card px-3 py-2 font-mono text-[11.5px] leading-relaxed text-muted-foreground">
          {source}
        </pre>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="mermaid-render grid w-full place-items-center overflow-x-auto"
      // 렌더된 SVG 를 직접 주입(mermaid 출력은 신뢰된 라이브러리 산출물).
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
