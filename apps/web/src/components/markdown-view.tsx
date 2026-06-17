"use client";

import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";

// react-markdown + GFM + sanitize 렌더 파이프라인.
// 시각 스타일은 순수 Tailwind로 각 요소를 매핑한다(.markdown-body 전역 CSS 의존 제거).
// onLinkClick: 본문 링크 클릭을 상위(viewer-panel)가 가로채 해석하도록 위임한다.
//   - 외부 새 탭/내부 열람/무시 처리는 viewer-panel이 담당.
//   - 콜백이 없으면 기본 a 태그 동작(새 탭)을 유지한다.

// 요소별 Tailwind 타이포그래피. 제목/리스트/인용/코드/표를 또렷한 위계로.
function buildComponents(onLinkClick?: (href: string) => void): Components {
  return {
    h1: ({ children, ...rest }) => (
      <h1 {...rest} className="mt-5 mb-2 text-[1.6em] font-extrabold leading-tight tracking-tight first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children, ...rest }) => (
      <h2 {...rest} className="mt-5 mb-2 text-[1.35em] font-bold leading-tight tracking-tight first:mt-0">
        {children}
      </h2>
    ),
    h3: ({ children, ...rest }) => (
      <h3 {...rest} className="mt-4 mb-1.5 text-[1.15em] font-bold leading-snug first:mt-0">
        {children}
      </h3>
    ),
    h4: ({ children, ...rest }) => (
      <h4 {...rest} className="mt-4 mb-1.5 text-[1em] font-semibold leading-snug first:mt-0">
        {children}
      </h4>
    ),
    p: ({ children, ...rest }) => (
      <p {...rest} className="my-2.5 leading-relaxed first:mt-0 last:mb-0">
        {children}
      </p>
    ),
    ul: ({ children, ...rest }) => (
      <ul {...rest} className="my-2.5 list-disc space-y-1 pl-5 marker:text-muted-foreground">
        {children}
      </ul>
    ),
    ol: ({ children, ...rest }) => (
      <ol {...rest} className="my-2.5 list-decimal space-y-1 pl-5 marker:text-muted-foreground">
        {children}
      </ol>
    ),
    li: ({ children, ...rest }) => (
      <li {...rest} className="leading-relaxed [&>ul]:my-1 [&>ol]:my-1">
        {children}
      </li>
    ),
    a: ({ href, children, ...rest }: ComponentPropsWithoutRef<"a">) => (
      <a
        {...rest}
        href={href ?? "#"}
        {...(onLinkClick
          ? {
              onClick: (e) => {
                e.preventDefault();
                if (href) onLinkClick(href);
              },
            }
          : { target: "_blank", rel: "noopener noreferrer" })}
        className="font-medium text-primary underline decoration-primary/40 underline-offset-2 hover:decoration-primary"
      >
        {children}
      </a>
    ),
    blockquote: ({ children, ...rest }) => (
      <blockquote
        {...rest}
        className="my-3 border-l-[3px] border-border pl-3 text-muted-foreground italic"
      >
        {children}
      </blockquote>
    ),
    hr: (rest) => <hr {...rest} className="my-5 border-border" />,
    strong: ({ children, ...rest }) => (
      <strong {...rest} className="font-semibold text-foreground">
        {children}
      </strong>
    ),
    em: ({ children, ...rest }) => (
      <em {...rest} className="italic">
        {children}
      </em>
    ),
    // 인라인 코드: 알약형 배경. 블록(pre 내부) 코드는 아래 pre에서 배경/패딩을 해제한다.
    code: ({ children, ...rest }) => (
      <code
        {...rest}
        className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.88em] text-foreground"
      >
        {children}
      </code>
    ),
    // 코드 블록: 어두운 표면 + 가로 스크롤. 내부 code의 인라인 스타일을 무력화한다.
    pre: ({ children, ...rest }) => (
      <pre
        {...rest}
        className="my-3 overflow-x-auto rounded-lg bg-[hsl(var(--code-bg))] p-3 text-[0.85em] leading-relaxed text-[hsl(var(--code-fg))] [&_code]:bg-transparent [&_code]:p-0 [&_code]:text-inherit"
      >
        {children}
      </pre>
    ),
    table: ({ children, ...rest }) => (
      <div className="my-3 overflow-x-auto">
        <table {...rest} className="w-full border-collapse text-[0.92em]">
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...rest }) => (
      <thead {...rest} className="bg-secondary">
        {children}
      </thead>
    ),
    th: ({ children, ...rest }) => (
      <th {...rest} className="border border-border px-2.5 py-1.5 text-left font-semibold">
        {children}
      </th>
    ),
    td: ({ children, ...rest }) => (
      <td {...rest} className="border border-border px-2.5 py-1.5">
        {children}
      </td>
    ),
    img: ({ ...rest }: ComponentPropsWithoutRef<"img">) => (
      // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
      <img {...rest} className="my-3 max-w-full rounded-lg border border-border" />
    ),
  };
}

export function MarkdownView({
  source,
  onLinkClick,
}: {
  source: string;
  onLinkClick?: (href: string) => void;
}) {
  return (
    <div className="text-[14px] leading-relaxed text-foreground [overflow-wrap:anywhere]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={buildComponents(onLinkClick)}
      >
        {source}
      </ReactMarkdown>
    </div>
  );
}
