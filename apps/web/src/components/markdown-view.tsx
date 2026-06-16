"use client";

import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

// board-simple과 동일한 렌더 파이프라인: react-markdown + GFM + sanitize.
// 시각 스타일은 globals.css의 .markdown-body가 담당한다.
// onLinkClick: 본문 링크 클릭을 상위(viewer-panel)가 가로채 해석하도록 위임한다.
//   - 반환 처리(외부 새 탭/내부 열람/무시)는 viewer-panel이 담당.
//   - 콜백이 없으면 기존 동작(기본 a 태그)을 유지한다.
export function MarkdownView({
  source,
  onLinkClick,
}: {
  source: string;
  onLinkClick?: (href: string) => void;
}) {
  return (
    <div className="markdown-body text-[14px] leading-relaxed text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={
          onLinkClick
            ? {
                // 모든 링크 클릭을 가로채 상위 콜백으로 위임(앱 네비게이션/외부 이동 차단).
                a: ({ href, children, ...rest }: ComponentPropsWithoutRef<"a">) => (
                  <a
                    {...rest}
                    href={href ?? "#"}
                    onClick={(e) => {
                      e.preventDefault();
                      if (href) onLinkClick(href);
                    }}
                  >
                    {children}
                  </a>
                ),
              }
            : undefined
        }
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
