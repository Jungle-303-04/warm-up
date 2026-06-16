"use client";

import { useEffect, useState } from "react";

import { getMe, loginUrl, type Me } from "../lib/api";
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
    return (
      <span
        title={`GitHub: ${me.login}`}
        className="inline-flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-3 text-[13px] font-medium text-foreground shadow-elev-1"
      >
        <img
          src={`https://avatars.githubusercontent.com/u/${me.user_id}`}
          alt={me.login}
          width={22}
          height={22}
          className="rounded-full"
        />
        {me.login}
      </span>
    );
  }

  return (
    <a
      href={loginUrl()}
      className="interactive inline-flex items-center gap-1.5 rounded-full bg-primary px-3.5 py-2 text-[13px] font-medium text-primary-foreground shadow-elev-1 hover:opacity-90 hover:shadow-elev-2 active:scale-[0.98]"
    >
      <Icon name="github" size={16} /> GitHub로 로그인
    </a>
  );
}
