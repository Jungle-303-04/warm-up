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
        className="inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[13px] text-foreground"
      >
        <Icon name="account_circle" size={18} className="text-primary" />
        {me.login}
      </span>
    );
  }

  return (
    <a
      href={loginUrl()}
      className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1.5 text-[13px] font-medium text-primary-foreground transition-opacity hover:opacity-90"
    >
      <Icon name="login" size={16} /> GitHub로 로그인
    </a>
  );
}
