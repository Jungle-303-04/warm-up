import path from "node:path";
import { existsSync } from "node:fs";

const workspaceRoot = path.join(import.meta.dirname, "..", "..");
const isWorkspaceBuild = existsSync(path.join(workspaceRoot, "pnpm-workspace.yaml"));

const nextConfig = {
  output: "standalone",
  // 좌하단 Next.js 개발 인디케이터(N 버튼) 숨김.
  devIndicators: false,
  async rewrites() {
    const backendProxyUrl = process.env.BACKEND_PROXY_URL?.replace(/\/$/, "");
    if (!backendProxyUrl) return [];
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendProxyUrl}/:path*`,
      },
    ];
  },
};

if (isWorkspaceBuild) {
  // 모노레포 루트를 명시해 멀티 lockfile 추론 경고를 제거한다.
  nextConfig.outputFileTracingRoot = workspaceRoot;
}

export default nextConfig;
