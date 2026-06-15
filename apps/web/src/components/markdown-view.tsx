"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

// board-simple과 동일한 렌더 파이프라인: react-markdown + GFM + sanitize.
// 시각 스타일은 globals.css의 .markdown-body가 담당한다.
export function MarkdownView({ source }: { source: string }) {
  return (
    <div className="markdown-body text-[14px] leading-relaxed text-foreground">
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
        {source}
      </ReactMarkdown>
    </div>
  );
}
