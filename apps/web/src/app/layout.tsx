import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RepoLM",
  description: "팀 저장소를 인덱싱해 근거 기반으로 답하고 제안하는 워크스페이스",
};

// 페인트 전에 테마 클래스를 결정해 FOUC(깜빡임) 방지. 기본값은 시스템 모드.
const themeBootstrap = `
(function () {
  try {
    var pref = localStorage.getItem("repolm-theme") || "system";
    var dark = pref === "dark" || (pref === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.classList.add(dark ? "dark" : "light");
  } catch (e) {
    document.documentElement.classList.add("light");
  }
})();
`;

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
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..24,400,0,0&display=swap"
        />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className="bg-bg text-ink font-sans antialiased">{children}</body>
    </html>
  );
}
