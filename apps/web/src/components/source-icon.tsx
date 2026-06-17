"use client";

import { useEffect, useState } from "react";

import { Icon } from "./icon";

// URL에서 호스트명을 추출함 파싱 실패 시 null.
function hostFromUrl(url?: string | null): string | null {
  if (!url) return null;
  try {
    return new URL(url.includes("://") ? url : `https://${url}`).hostname;
  } catch {
    return null;
  }
}

// 소스 종류 아이콘을 공유하는 재사용 컴포넌트.
// - URL 소스: 사이트 favicon(google s2)을 <img>로 표시, 로드 실패 시 link 아이콘 폴백.
// - 그 외(md/pdf/text/repo, 파일 확장자): 정적 lucide 아이콘.
// 소스행·인용칩·뷰어헤더가 모두 이 컴포넌트를 공유함
export function SourceIcon({
  iconName,
  url,
  size = 14,
  className = "",
  isUrl = false,
}: {
  // 정적 아이콘 이름(SOURCE_KINDS[kind].icon 또는 fileIconForPath 결과).
  iconName: string;
  // URL 소스일 때 favicon 추출에 쓰는 원문 URL.
  url?: string | null;
  size?: number;
  className?: string;
  // 명시적으로 URL 소스임을 표시(url이 없어도 link 폴백을 쓰도록).
  isUrl?: boolean;
}) {
  const host = hostFromUrl(url);
  // favicon 로드 실패 시 link 아이콘으로 폴백.
  const [faviconFailed, setFaviconFailed] = useState(false);

  // host가 바뀌면 실패 상태를 초기화해 새 사이트의 favicon을 다시 시도함
  useEffect(() => {
    setFaviconFailed(false);
  }, [host]);

  // URL 소스이고 호스트를 얻었고 아직 실패하지 않았으면 favicon을 시도.
  if (host && !faviconFailed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        // host 변경 시 강제로 새 <img>를 만들어 onError 상태 꼬임을 방지.
        key={host}
        src={`https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://${host}&size=64`}
        alt=""
        // 작은 아이콘은 즉시 로드(지연 로드 시 안 뜨는 케이스 방지).
        loading="eager"
        decoding="async"
        referrerPolicy="no-referrer"
        onError={() => setFaviconFailed(true)}
        className={className}
        // 인라인 블록 + contain으로 작은 박스 안에 또렷하게 맞춤
        style={{
          width: size,
          height: size,
          objectFit: "contain",
          borderRadius: 3,
          display: "block",
          flexShrink: 0,
        }}
      />
    );
  }

  // URL 소스인데 favicon이 없거나 실패하면 link 아이콘으로 폴백.
  if (isUrl) {
    return <Icon name="link" size={size} className={className} />;
  }

  // 정적 아이콘.
  return <Icon name={iconName} size={size} className={className} />;
}
