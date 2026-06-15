"use client";

import { useEffect, useState } from "react";

import { getMe, loginUrl, type Me } from "../lib/api";
import { Icon } from "./icon";

export function AuthMenu() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <span className="grid h-8 w-8 place-items-center text-muted-foreground">
        <Icon name="progress_activity" className="animate-spin text-[18px]" />
      </span>
    );
  }

  if (me) {
    return (
      <span
        title={`GitHub: ${me.login}`}
        className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[13px] text-foreground"
      >
        <Icon name="account_circle" className="text-[18px] text-primary" />
        {me.login}
      </span>
    );
  }

  return (
    <a
      href={loginUrl()}
      className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1.5 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
    >
      <Icon name="login" className="text-[16px]" /> GitHub로 로그인
    </a>
  );
}
