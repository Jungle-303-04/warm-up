"use client";

import { useEffect, useId, useRef, useState } from "react";

import { Button } from "./ui/button";

// svg-pan-zoom은 `export = svgPanZoom`(Instance 타입의 const)이라 기본 import 값의
// 타입이 곧 인스턴스 타입이다. 런타임에선 이 값이 팩토리 함수로도 동작하므로
// 호출 시 팩토리 시그니처로 캐스팅해 사용한다.
type PanZoomInstance = typeof import("svg-pan-zoom");
type PanZoomFactory = (svg: SVGElement, options?: Record<string, unknown>) => PanZoomInstance;

// 현재 문서 테마(.dark 클래스)에 따라 mermaid 테마를 고른다.
function isDarkTheme(): boolean {
  if (typeof document === "undefined") return false;
  return document.documentElement.classList.contains("dark");
}

// 렌더된 Mermaid SVG에 줌·팬을 입히는 캔버스. svg-pan-zoom을 동적 import 해
// 클라이언트에서만 적용한다(SSR 안전). svg가 바뀌면 인스턴스를 재생성한다.
function PanZoomCanvas({ svg }: { svg: string }) {
  const hostRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<PanZoomInstance | null>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !svg) return;
    let disposed = false;
    let resizeObs: ResizeObserver | null = null;

    // 주입된 SVG 요소를 찾아 pan-zoom을 적용한다.
    (async () => {
      // mermaid SVG는 보통 max-width 인라인 스타일을 갖는데, 이는 캔버스 채움을 막는다.
      const svgEl = host.querySelector("svg");
      if (!svgEl) return;
      // 컨테이너를 가득 채우도록 크기/스타일 보정.
      svgEl.setAttribute("width", "100%");
      svgEl.setAttribute("height", "100%");
      svgEl.style.maxWidth = "100%";
      svgEl.style.maxHeight = "100%";
      svgEl.style.display = "block";

      // 동적 import: 클라이언트에서만 svg-pan-zoom 로드(esModuleInterop → default).
      const mod = await import("svg-pan-zoom");
      const svgPanZoom = (mod.default ?? (mod as unknown)) as PanZoomFactory;
      if (disposed) return;

      try {
        instanceRef.current = svgPanZoom(svgEl, {
          zoomEnabled: true,
          panEnabled: true,
          controlIconsEnabled: false, // 자체 컨트롤 버튼 사용.
          dblClickZoomEnabled: true,
          mouseWheelZoomEnabled: true,
          preventMouseEventsDefault: true,
          fit: true,
          center: true,
          minZoom: 0.2,
          maxZoom: 12,
          zoomScaleSensitivity: 0.3,
        });
      } catch {
        // pan-zoom 적용 실패해도 정적 SVG는 그대로 보인다(폴백).
        instanceRef.current = null;
      }

      // 컨테이너 크기는 flex 레이아웃이 늦게 확정될 수 있다. 초기 fit이 작은
      // 박스 기준으로 굳지 않도록, 크기 변화 때마다 resize→fit→center로 다시 맞춘다
      // (세로로 꽉 차게 보이지 않던 문제 해결).
      const refit = () => {
        const inst = instanceRef.current;
        if (!inst) return;
        try {
          inst.resize();
          inst.fit();
          inst.center();
        } catch {
          // 레이아웃 전환 중 일시적 실패는 무시.
        }
      };
      // 다음 프레임에 한 번(초기 레이아웃 확정 후) + 이후 크기 변화마다.
      requestAnimationFrame(refit);
      if (typeof ResizeObserver !== "undefined") {
        resizeObs = new ResizeObserver(refit);
        resizeObs.observe(host);
      }
    })();

    return () => {
      disposed = true;
      resizeObs?.disconnect();
      try {
        instanceRef.current?.destroy();
      } catch {
        // 이미 제거된 경우 무시.
      }
      instanceRef.current = null;
    };
  }, [svg]);

  // 컨트롤 버튼 동작. 인스턴스가 없으면(폴백) 무시.
  const zoomIn = () => instanceRef.current?.zoomIn();
  const zoomOut = () => instanceRef.current?.zoomOut();
  const reset = () => {
    const inst = instanceRef.current;
    if (!inst) return;
    inst.resetZoom();
    inst.center();
    inst.fit();
  };

  return (
    // 카드/테두리 없이 부모(relative) 영역을 absolute로 가로·세로 꽉 채운다.
    // h-full 백분율 높이가 flex 체인에서 흔들리는 문제를 inset-0로 확실히 회피한다.
    <div className="absolute inset-0 overflow-hidden">
      {/* 줌·팬 대상 SVG 호스트. svg는 신뢰된 mermaid 출력. */}
      <div
        ref={hostRef}
        className="mermaid-render h-full w-full cursor-grab active:cursor-grabbing"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
      {/* 작은 컨트롤 버튼(확대/축소/리셋). 우하단 고정. */}
      <div className="absolute bottom-2 right-2 flex items-center gap-1 rounded-full border border-border bg-card/90 p-1 shadow-sm backdrop-blur">
        <Button
          variant="ghost"
          size="xs"
          pill={false}
          icon="add"
          onClick={zoomIn}
          aria-label="확대"
          title="확대"
          className="h-6 w-6 px-0"
        />
        <Button
          variant="ghost"
          size="xs"
          pill={false}
          icon="remove"
          onClick={zoomOut}
          aria-label="축소"
          title="축소"
          className="h-6 w-6 px-0"
        />
        <Button
          variant="ghost"
          size="xs"
          pill={false}
          icon="refresh"
          onClick={reset}
          aria-label="맞춤(리셋)"
          title="화면에 맞춤"
          className="h-6 w-6 px-0"
        />
      </div>
    </div>
  );
}

// Mermaid 다이어그램을 동적 import 로 렌더한다(SSR 안전).
// 렌더 성공 시 줌·팬 캔버스로 보여주고, 실패 시 onError 로 에러를 위임해
// 호출부가 원본 소스를 노출하게 한다.
export function MermaidRender({
  source,
  onError,
}: {
  source: string;
  // 렌더 성공/실패를 호출부에 알린다(null = 성공).
  onError?: (message: string | null) => void;
}) {
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
        <pre className="max-h-72 overflow-auto rounded-lg border border-border bg-card px-3 py-2 font-mono text-[11.5px] leading-relaxed text-muted-foreground">
          {source}
        </pre>
      </div>
    );
  }

  if (!svg) return null;

  // svg가 바뀌면 캔버스를 새로 마운트(key)해 pan-zoom 인스턴스를 깔끔히 재생성.
  return <PanZoomCanvas key={svg} svg={svg} />;
}
