"use client";

import { useEffect, useRef, useState } from "react";

import { getMe, loginUrl, logout, type Me } from "../lib/api";
import { Icon } from "./icon";

export function AuthMenu() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getMe(controller.signal)
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  if (loading) {
    return (
      <span className="grid h-8 w-8 place-items-center text-muted-foreground">
        <Icon name="progress_activity" size={18} className="animate-spin" />
      </span>
    );
  }

  if (me) {
    return <ProfileMenu me={me} />;
  }

  return (
    <a
      href={loginUrl()}
      className="transition-all duration-200 ease-in-out inline-flex items-center gap-1.5 rounded-full bg-primary px-3.5 py-2 text-[13px] font-medium text-primary-foreground shadow-sm hover:opacity-90 hover:shadow active:scale-[0.98]"
    >
      <Icon name="github" size={16} /> GitHub로 로그인
    </a>
  );
}

// 로그인 상태에서 아바타+이름을 버튼으로 만들고, 클릭 시 팝업 메뉴를 표시
// 메뉴에는 (상단) 프로필 요약 + GitHub 프로필 링크, (하단) 로그아웃 항목이 있음
function ProfileMenu({ me }: { me: Me }) {
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const avatarUrl = `https://avatars.githubusercontent.com/u/${me.user_id}`;
  const profileUrl = `https://github.com/${me.login}`;

  // 바깥 클릭/Esc로 메뉴 닫기.
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // 로그아웃 → 서버 쿠키 만료 후 로그인 화면(AuthGate)으로 이동.
  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      // 실패해도 화면을 새로고침해 로그인 게이트로 보낸다(쿠키가 이미 만료됐을 수 있음).
    }
    window.location.href = "/";
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title={`GitHub: ${me.login}`}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`${me.login} 프로필 메뉴`}
        className="transition-all duration-200 ease-in-out inline-flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-2.5 text-[13px] font-medium text-foreground shadow-sm hover:bg-secondary active:scale-[0.98]"
      >
        <img
          src={avatarUrl}
          alt={me.login}
          width={22}
          height={22}
          className="rounded-full"
        />
        {me.login}
        <Icon
          name="expand_more"
          size={15}
          className={`text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open ? (
        <div
          role="menu"
          aria-label="프로필"
          className="absolute right-0 top-full z-20 mt-1.5 w-60 overflow-hidden rounded-xl border border-border bg-card py-1 shadow"
        >
          {/* 상단: 아바타 + 로그인명 + GitHub 프로필 링크(새 탭) */}
          <a
            role="menuitem"
            href={profileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="transition-all duration-200 ease-in-out flex items-center gap-2.5 px-3 py-2.5 hover:bg-secondary"
          >
            <img
              src={avatarUrl}
              alt={me.login}
              width={36}
              height={36}
              className="rounded-full"
            />
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[13px] font-semibold leading-tight text-foreground">
                {me.login}
              </span>
              <span className="mt-0.5 flex items-center gap-1 text-[11px] text-muted-foreground">
                <Icon name="github" size={12} /> GitHub 프로필 열기
                <Icon name="north_east" size={11} />
              </span>
            </span>
          </a>

          <div className="my-1 h-px bg-border" />

          {/* 하단: 로그아웃 */}
          <button
            type="button"
            role="menuitem"
            onClick={() => void handleLogout()}
            disabled={loggingOut}
            className="transition-all duration-200 ease-in-out flex w-full items-center gap-2 px-3 py-2 text-left text-[12.5px] font-medium text-destructive hover:bg-destructive/10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Icon
              name={loggingOut ? "progress_activity" : "logout"}
              size={15}
              className={loggingOut ? "animate-spin" : ""}
            />
            {loggingOut ? "로그아웃 중…" : "로그아웃"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
