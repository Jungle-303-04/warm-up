import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoLM",
  description: "팀 저장소를 인덱싱해 근거 기반으로 답하고 제안하는 워크스페이스",
};

// 페인트 전에 테마 클래스를 결정해 FOUC(깜빡임) 방지. 기본값 = 시스템(O3).
const themeBootstrap = `(function(){try{var p=localStorage.getItem("repolm-theme")||"system";var d=p==="dark"||(p==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.add(d?"dark":"light");}catch(e){document.documentElement.classList.add("light");}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap"
        />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className="bg-background text-foreground font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
