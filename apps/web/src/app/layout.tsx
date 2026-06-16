import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoLM",
  description: "팀 저장소를 인덱싱해 근거 기반으로 답하고 제안하는 워크스페이스",
};

// 페인트 전에 테마 클래스를 결정해 FOUC(깜빡임) 방지. 기본값 = 시스템.
const themeBootstrap = `(function(){try{var p=localStorage.getItem("repolm-theme")||"system";var d=p==="dark"||(p==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);var el=document.documentElement;el.classList.toggle("dark",d);el.classList.toggle("light",!d);}catch(e){document.documentElement.classList.add("light");}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://cdn.jsdelivr.net" crossOrigin="anonymous" />
        {/* velog 느낌의 한글 UI 폰트(Pretendard, 오픈소스) + 코드용 모노 */}
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
        />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className="bg-background text-foreground font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
