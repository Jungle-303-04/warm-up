# pnpm 사용법과 관련 파일 라인별 해설

이 문서는 현재 RepoLM web workspace에서 pnpm이 어떻게 쓰이는지 설명한다.

`pnom`이라고 부른 부분은 이 문서에서 `pnpm`으로 정리한다.

## pnpm이 하는 일

pnpm은 JavaScript/TypeScript package manager다.

현재 프로젝트에서는 다음 일을 한다.

```text
1. Next.js/React 의존성을 설치한다.
2. apps/web package script를 실행한다.
3. workspace 안의 특정 package만 골라 실행한다.
4. pnpm-lock.yaml로 dependency version을 고정한다.
```

## 관련 파일

현재 사람이 직접 읽고 수정하는 pnpm 관련 파일은 다음이다.

```text
package.json
pnpm-workspace.yaml
apps/web/package.json
apps/web/Dockerfile
.mise.toml
```

자동 생성 파일은 다음이다.

```text
pnpm-lock.yaml
```

`pnpm-lock.yaml`은 직접 편집하지 않는다.
`pnpm install`, `pnpm add`, `pnpm remove` 같은 명령 결과로 바뀐다.

## 루트 `package.json`

전체 파일:

```json
{
  "name": "repolm-workspace",
  "private": true,
  "packageManager": "pnpm@10.17.0",
  "engines": {
    "node": ">=22.12"
  },
  "scripts": {
    "dev": "pnpm --filter @repolm/web dev",
    "build": "pnpm --filter @repolm/web build",
    "typecheck": "pnpm --filter @repolm/web typecheck"
  }
}
```

라인별 설명:

- 1: JSON 객체를 시작한다.
- 2: workspace root package 이름이다. 배포용 package라기보다 workspace 전체 이름이다.
- 3: `private: true`라서 npm registry에 publish하지 않는다.
- 4: 이 workspace가 pnpm 10.17.0을 사용한다고 명시한다. Corepack이 이 값을 보고 맞는 pnpm을 사용할 수 있다.
- 5: Node.js engine 조건을 적는 객체를 시작한다.
- 6: Node.js는 22.12 이상이어야 한다고 선언한다.
- 7: `engines` 객체를 닫는다.
- 8: root에서 실행할 script 목록을 시작한다.
- 9: `pnpm dev`를 실행하면 `@repolm/web` package의 `dev` script를 실행한다.
- 10: `pnpm build`를 실행하면 `@repolm/web` package의 `build` script를 실행한다.
- 11: `pnpm typecheck`를 실행하면 `@repolm/web` package의 `typecheck` script를 실행한다.
- 12: `scripts` 객체를 닫는다.
- 13: JSON 객체를 닫는다.

핵심은 `--filter`다.

```bash
pnpm --filter @repolm/web dev
```

이 명령은 workspace 전체 중에서 이름이 `@repolm/web`인 package만 골라 `dev`를 실행한다.

## `pnpm-workspace.yaml`

전체 파일:

```yaml
packages:
  - "apps/*"
```

라인별 설명:

- 1: pnpm workspace에 포함할 package 목록을 시작한다.
- 2: `apps/` 바로 아래의 모든 폴더를 workspace package 후보로 포함한다.
- 3: 파일 끝의 빈 줄이다.

현재 구조에서는 `apps/web/package.json`이 있으므로 `apps/web`이 workspace package가 된다.

즉 pnpm은 다음처럼 이해한다.

```text
root package
└── apps/web package = @repolm/web
```

## `apps/web/package.json`

전체 파일:

```json
{
  "name": "@repolm/web",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.8.0"
  }
}
```

라인별 설명:

- 1: JSON 객체를 시작한다.
- 2: web package 이름이다. root `package.json`의 `--filter @repolm/web`이 이 이름을 찾는다.
- 3: web package version이다.
- 4: 이 package도 publish하지 않는다.
- 5: JavaScript module 방식을 ESM으로 쓴다는 뜻이다.
- 6: web package script 목록을 시작한다.
- 7: `next dev`로 개발 서버를 실행한다.
- 8: `next build`로 production build를 만든다.
- 9: `next start`로 production server를 실행한다.
- 10: TypeScript compiler를 실행하되 파일은 생성하지 않고 타입 검사만 한다.
- 11: scripts 객체를 닫는다.
- 12: runtime dependency 목록을 시작한다.
- 13: Next.js framework dependency다.
- 14: React dependency다.
- 15: React DOM renderer dependency다.
- 16: runtime dependency 객체를 닫는다.
- 17: 개발 중 필요한 dependency 목록을 시작한다.
- 18: Node.js type definition이다.
- 19: React type definition이다.
- 20: React DOM type definition이다.
- 21: TypeScript compiler다.
- 22: dev dependency 객체를 닫는다.
- 23: JSON 객체를 닫는다.
- 24: 파일 끝의 빈 줄이다.

## `apps/web/Dockerfile` 안의 pnpm

전체 파일:

```dockerfile
FROM node:24-alpine AS base
WORKDIR /repo
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --filter @repolm/web --frozen-lockfile

COPY apps/web apps/web

EXPOSE 3000
CMD ["pnpm", "--filter", "@repolm/web", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
```

라인별 설명:

- 1: Node.js 24 alpine image를 사용한다.
- 2: container 안의 작업 디렉터리를 `/repo`로 둔다.
- 3: Corepack을 켜서 `packageManager`에 맞는 pnpm을 사용할 수 있게 한다.
- 4: 빈 줄이다.
- 5: root package, pnpm lockfile, workspace 파일을 container로 복사한다.
- 6: web package manifest를 container로 복사한다.
- 7: `@repolm/web` package에 필요한 의존성을 lockfile 기준으로 설치한다.
- 8: 빈 줄이다.
- 9: 실제 web app source를 container에 복사한다.
- 10: 빈 줄이다.
- 11: container가 3000번 port를 사용한다고 문서화한다.
- 12: web package의 `dev` script를 실행하고, 외부 접속을 위해 host를 `0.0.0.0`으로 둔다.
- 13: 파일 끝의 빈 줄이다.

여기서 `--frozen-lockfile`은 중요하다.

```bash
pnpm install --frozen-lockfile
```

뜻은 다음과 같다.

```text
pnpm-lock.yaml과 package.json이 맞지 않으면 lockfile을 고치지 말고 실패해.
```

Docker image build에서는 dependency version이 임의로 바뀌면 안 되므로 이 옵션을 쓴다.

## `.mise.toml` 안의 pnpm

pnpm 관련 줄은 다음이다.

```toml
pnpm = "10.17.0"
```

pnpm version을 mise가 고정한다.

```toml
"corepack enable",
```

Corepack을 활성화해 `packageManager`에 적힌 pnpm을 안정적으로 쓰게 한다.

```toml
"pnpm install",
```

workspace dependency를 설치한다.

```toml
run = "pnpm --filter @repolm/web typecheck"
```

web package만 골라 typecheck를 실행한다.

## `pnpm-lock.yaml`

`pnpm-lock.yaml`은 581줄의 자동 생성 파일이다.

직접 라인별로 편집하거나 외우는 대상이 아니다.
대신 다음 구조를 이해하면 된다.

```yaml
lockfileVersion: '9.0'
```

lockfile 포맷 버전이다.

```yaml
settings:
  autoInstallPeers: true
  excludeLinksFromLockfile: false
```

pnpm install 설정이다.

```yaml
importers:

  .: {}

  apps/web:
    dependencies:
      next:
        specifier: ^15.0.0
        version: 15.5.19(...)
```

`importers`는 workspace package별 직접 dependency를 기록한다.

현재는 root와 `apps/web`이 있다.

```yaml
packages:

  '@emnapi/runtime@1.11.0':
    resolution: {integrity: ...}
```

`packages` 아래에는 실제 설치될 모든 하위 dependency와 integrity hash가 기록된다.

이 파일의 목적은 다음이다.

```text
package.json: 내가 원하는 dependency 범위
pnpm-lock.yaml: 실제로 설치된 정확한 dependency version
```

예를 들어 `apps/web/package.json`에는 이렇게 적혀 있다.

```json
"next": "^15.0.0"
```

`^15.0.0`은 15.x 범위 안에서 업데이트될 수 있다는 뜻이다.

하지만 lockfile에는 실제 설치된 버전이 고정된다.

```yaml
version: 15.5.19
```

그래서 다른 사람이 `pnpm install`을 해도 같은 dependency tree를 받을 수 있다.

## 자주 쓰는 pnpm 명령

```bash
pnpm install
```

workspace dependency를 설치한다.

```bash
pnpm --filter @repolm/web dev
```

web 개발 서버를 실행한다.

```bash
pnpm --filter @repolm/web build
```

web production build를 만든다.

```bash
pnpm --filter @repolm/web typecheck
```

web TypeScript typecheck를 실행한다.

```bash
pnpm add <package> --filter @repolm/web
```

web package에 runtime dependency를 추가한다.

```bash
pnpm add -D <package> --filter @repolm/web
```

web package에 dev dependency를 추가한다.

## 현재 구조에서 주의할 점

새 frontend app을 추가하면 `apps/*` 아래에 package를 만들면 된다.

예를 들어:

```text
apps/admin/package.json
```

그러면 `pnpm-workspace.yaml`의 `"apps/*"` 규칙에 의해 workspace package가 된다.

root script에서 실행하려면 root `package.json`에 script를 추가한다.

```json
"admin:dev": "pnpm --filter @repolm/admin dev"
```

dependency를 추가할 때는 root에 막 추가하지 말고, 실제로 필요한 package에 추가한다.

```bash
pnpm add lucide-react --filter @repolm/web
```

이렇게 해야 dependency 소유가 분명해진다.
