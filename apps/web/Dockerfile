FROM node:24-alpine AS base
WORKDIR /repo
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --filter @repopilot/web --frozen-lockfile

COPY apps/web apps/web

EXPOSE 3000
CMD ["pnpm", "--filter", "@repopilot/web", "dev", "--hostname", "0.0.0.0", "--port", "3000"]

