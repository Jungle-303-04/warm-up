"use client";

import { useEffect, useState } from "react";

import { getMe, loginUrl, type Me } from "../lib/api";
import { Icon } from "./icon";
import { ThemeToggle } from "./theme-toggle";

// 로그인 안내 화면. 미로그인/세션 만료 시 표시한다.
// 모든 노트북/소스/채팅/산출물 API가 세션을 요구하므로, 진입 전 로그인으로 유도한다.
export function LoginScreen() {
  return (
    <div className="relative grid min-h-screen place-items-center bg-background px-6 text-foreground">
      <div className="absolute right-5 top-5">
        <ThemeToggle />
      </div>
      <div className="flex w-full max-w-sm flex-col items-center text-center">
        <span className="grid h-14 w-14 place-items-center rounded-2xl bg-accent text-accent-foreground shadow-elev-1">
          <Icon name="hub" size={28} />
        </span>
        <h1 className="mt-5 text-[22px] font-semibold tracking-tight">RepoLM</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
          저장소·문서를 근거로 질문하고 다이어그램을 생성하는 워크스페이스.
          <br />
          시작하려면 GitHub로 로그인하세요.
        </p>
        <a
          href={loginUrl()}
          className="interactive mt-6 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-[13px] font-semibold text-primary-foreground shadow-elev-1 hover:opacity-90 hover:shadow-elev-2 active:scale-[0.98]"
        >
          <Icon name="github" size={17} /> GitHub로 로그인
        </a>
      </div>
    </div>
  );
}

// 인증 게이트: 로그인 상태를 확인해 미로그인이면 로그인 화면, 로그인이면 children.
export function AuthGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "authed" | "anon">("loading");

  useEffect(() => {
    const controller = new AbortController();
    getMe(controller.signal)
      .then((me: Me | null) => setState(me ? "authed" : "anon"))
      .catch(() => setState("anon"));
    return () => controller.abort();
  }, []);

  if (state === "loading") {
    return (
      <div className="grid min-h-screen place-items-center bg-background text-muted-foreground">
        <Icon name="progress_activity" size={26} className="animate-spin" />
      </div>
    );
  }

  if (state === "anon") return <LoginScreen />;

  return <>{children}</>;
}
