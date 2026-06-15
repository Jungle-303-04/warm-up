import path from "node:path";

const nextConfig = {
  output: "standalone",
  // 모노레포 루트를 명시해 멀티 lockfile 추론 경고를 제거한다.
  outputFileTracingRoot: path.join(import.meta.dirname, "..", ".."),
  // 좌하단 Next.js 개발 인디케이터(N 버튼) 숨김.
  devIndicators: false,
};

export default nextConfig;
