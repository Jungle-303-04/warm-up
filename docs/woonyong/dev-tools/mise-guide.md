# mise 사용법

이 문서는 현재 프로젝트의 `.mise.toml`을 이해하기 위한 설명이다.

## mise가 하는 일

`mise`는 프로젝트별 개발 도구 버전과 반복 명령을 고정하는 도구다.

현재 프로젝트에서는 두 가지 일을 한다.

```text
1. Node.js, pnpm, Python, uv 버전을 고정한다.
2. setup, test, compose 실행 명령을 task로 묶는다.
```

그래서 팀원이 매번 긴 명령을 외우지 않아도 된다.

```bash
mise install
mise run setup
mise run check
mise run compose:up
```

## 전체 파일

```toml
[tools]
node = "24.16.0"
pnpm = "10.17.0"
python = "3.12"
uv = "0.9.17"

[tasks.setup]
description = "Install JavaScript and Python dependencies"
run = [
  "corepack enable",
  "pnpm install",
  "uv sync --project backend"
]

[tasks."compose:config"]
description = "Validate Docker Compose configuration"
run = "docker compose config --quiet"

[tasks."compose:up"]
description = "Start the local RepoPilot pipeline"
run = "docker compose up --build"

[tasks."compose:down"]
description = "Stop the local RepoPilot pipeline"
run = "docker compose down"

[tasks."compose:logs"]
description = "Follow pipeline logs"
run = "docker compose logs -f"

[tasks."api:test"]
description = "Run backend tests"
dir = "backend"
run = "uv run pytest"

[tasks."web:typecheck"]
description = "Type-check the web app"
run = "pnpm --filter @repopilot/web typecheck"

[tasks.check]
description = "Run lightweight local checks"
depends = ["compose:config", "api:test", "web:typecheck"]
```

## 라인별 설명

### 1-5줄: 도구 버전 고정

```toml
[tools]
```

1줄은 도구 버전 섹션을 시작한다.

```toml
node = "24.16.0"
```

2줄은 Node.js 버전을 24.16.0으로 고정한다.
Next.js, React, pnpm 실행에 필요하다.

```toml
pnpm = "10.17.0"
```

3줄은 pnpm 버전을 10.17.0으로 고정한다.
JavaScript 의존성 설치와 workspace script 실행에 쓴다.

```toml
python = "3.12"
```

4줄은 Python 버전을 3.12로 고정한다.
FastAPI backend 실행과 테스트에 쓴다.

```toml
uv = "0.9.17"
```

5줄은 uv 버전을 0.9.17로 고정한다.
Python dependency sync, virtualenv, pytest 실행에 쓴다.

## 7-13줄: setup task

```toml
[tasks.setup]
```

7줄은 `mise run setup`으로 실행할 task를 정의한다.

```toml
description = "Install JavaScript and Python dependencies"
```

8줄은 task 설명이다.

```toml
run = [
```

9줄은 여러 명령을 순서대로 실행하는 배열을 시작한다.

```toml
  "corepack enable",
```

10줄은 Corepack을 활성화한다.
Corepack은 Node.js에 포함된 package manager wrapper다.
`packageManager`에 적힌 pnpm 버전을 안정적으로 쓰게 해준다.

```toml
  "pnpm install",
```

11줄은 pnpm workspace 의존성을 설치한다.
루트 `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`을 기준으로 설치한다.

```toml
  "uv sync --project backend"
```

12줄은 backend Python 의존성을 동기화한다.
`backend/pyproject.toml`과 `backend/uv.lock` 기준으로 `.venv`를 만든다.

```toml
]
```

13줄은 명령 배열을 닫는다.

## 15-17줄: Compose 설정 검증

```toml
[tasks."compose:config"]
```

15줄은 `mise run compose:config` task를 정의한다.
이름에 `:`가 있어서 따옴표로 감싼다.

```toml
description = "Validate Docker Compose configuration"
```

16줄은 task 설명이다.

```toml
run = "docker compose config --quiet"
```

17줄은 Docker Compose 설정이 유효한지 검사한다.
문제가 없으면 출력 없이 끝난다.

## 19-21줄: Compose 실행

```toml
[tasks."compose:up"]
```

19줄은 `mise run compose:up` task를 정의한다.

```toml
description = "Start the local RepoPilot pipeline"
```

20줄은 local pipeline을 시작한다는 설명이다.

```toml
run = "docker compose up --build"
```

21줄은 compose 서비스를 실행한다.
`--build`가 있어서 web/api 이미지를 먼저 다시 빌드한다.

## 23-25줄: Compose 종료

```toml
[tasks."compose:down"]
```

23줄은 `mise run compose:down` task를 정의한다.

```toml
description = "Stop the local RepoPilot pipeline"
```

24줄은 local pipeline을 멈춘다는 설명이다.

```toml
run = "docker compose down"
```

25줄은 컨테이너와 네트워크를 내린다.
기본적으로 named volume은 지우지 않는다.

## 27-29줄: Compose 로그

```toml
[tasks."compose:logs"]
```

27줄은 `mise run compose:logs` task를 정의한다.

```toml
description = "Follow pipeline logs"
```

28줄은 로그를 따라본다는 설명이다.

```toml
run = "docker compose logs -f"
```

29줄은 모든 compose 서비스 로그를 실시간으로 출력한다.
`-f`는 follow라는 뜻이다.

## 31-34줄: Backend test

```toml
[tasks."api:test"]
```

31줄은 `mise run api:test` task를 정의한다.

```toml
description = "Run backend tests"
```

32줄은 backend test를 실행한다는 설명이다.

```toml
dir = "backend"
```

33줄은 명령 실행 전에 작업 디렉터리를 `backend`로 바꾼다.

```toml
run = "uv run pytest"
```

34줄은 uv 환경에서 pytest를 실행한다.

## 36-38줄: Web typecheck

```toml
[tasks."web:typecheck"]
```

36줄은 `mise run web:typecheck` task를 정의한다.

```toml
description = "Type-check the web app"
```

37줄은 web app typecheck를 실행한다는 설명이다.

```toml
run = "pnpm --filter @repopilot/web typecheck"
```

38줄은 pnpm workspace에서 `@repopilot/web` package만 골라 typecheck script를 실행한다.

## 40-42줄: 전체 가벼운 검증

```toml
[tasks.check]
```

40줄은 `mise run check` task를 정의한다.

```toml
description = "Run lightweight local checks"
```

41줄은 가벼운 local check라는 설명이다.

```toml
depends = ["compose:config", "api:test", "web:typecheck"]
```

42줄은 이 task가 직접 명령을 실행하지 않고 다른 task 3개를 순서대로 실행한다는 뜻이다.

실제로는 다음과 같다.

```bash
mise run compose:config
mise run api:test
mise run web:typecheck
```

## 자주 쓰는 명령

```bash
mise install
```

`.mise.toml`의 `[tools]`에 적힌 도구 버전을 설치한다.

```bash
mise run setup
```

JavaScript와 Python 의존성을 설치한다.

```bash
mise run check
```

Compose 설정, backend test, web typecheck를 한 번에 확인한다.

```bash
mise run compose:up
```

로컬 개발 환경 전체를 띄운다.

```bash
mise run compose:down
```

로컬 개발 환경을 내린다.

## 왜 필요한가

이 파일이 없으면 사람마다 실행 방식이 달라질 수 있다.

```text
pnpm i
npm install
python -m pytest
cd backend && pytest
docker-compose up
docker compose up
```

`mise`를 쓰면 프로젝트의 실행 계약이 하나로 고정된다.

```text
설치: mise run setup
검증: mise run check
실행: mise run compose:up
종료: mise run compose:down
```
