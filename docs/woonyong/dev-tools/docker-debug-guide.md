# Docker 컨테이너 디버그

## 왜 import 오류가 보였나

VS Code는 현재 repo root를 workspace로 본다.
Python 코드는 `backend/app` 아래에 있고 import는 `app.pipeline`처럼 `backend`를 import root로 가정한다.

테스트와 Docker는 `backend` 또는 `/app`을 기준으로 실행되기 때문에 import가 된다.
하지만 VS Code/Pylance가 `backend`를 분석 경로로 모르면 `Unable to import 'app.pipeline'`처럼 표시한다.

해결 기준:

- `pyrightconfig.json`에서 `backend`를 Python extra path로 등록한다.
- `.vscode/settings.json`에서 Python interpreter와 pytest cwd를 `backend` 기준으로 둔다.
- `backend/app` 하위 폴더는 namespace package로 동작한다. `__init__.py`는 export나 초기화 코드가 필요할 때만 둔다.
- `mise run check`에 Pyright 검사를 포함해 VS Code/Pylance가 보는 import 경로를 계속 확인한다.
- 자세한 기준은 [Python import root 기준](./python-import-root-guide.md)을 따른다.

## 컨테이너에서 실행하고 VS Code로 붙기

디버그 실행은 일반 Compose 파일에 `compose.debug.yaml`을 덧붙인다.

```bash
mise run compose:debug
```

FastAPI만 먼저 보고 싶으면 아래 명령을 쓴다.

```bash
mise run compose:debug:api
```

## FastAPI breakpoint

1. VS Code에서 breakpoint를 건다.
2. `mise run compose:debug`를 실행한다.
3. Run and Debug에서 `Attach FastAPI in Docker`를 선택한다.
4. 브라우저나 curl로 `http://localhost:8000`에 요청한다.

VS Code는 `localhost:5678`로 붙고, 컨테이너의 `/app` 경로를 로컬 `backend` 폴더에 매핑한다.

API 요청은 Swagger UI, REST Client, curl 중 편한 것을 쓴다.
구체적인 요청 예시는 [API 테스트 방법](./api-testing-guide.md)을 따른다.

## Next.js breakpoint

1. `mise run compose:debug`를 실행한다.
2. Run and Debug에서 `Attach Next.js in Docker`를 선택한다.
3. 브라우저에서 `http://localhost:3000`을 연다.

Next.js 디버거는 `localhost:9229`로 붙는다.

## 일반 실행과의 차이

일반 실행:

```bash
mise run compose:up
```

디버그 실행:

```bash
mise run compose:debug
```

일반 실행은 디버그 포트를 열지 않는다.
디버그 실행만 `api:5678`, `web:9229`를 추가로 연다.

## 재발 방지 규칙

Python import 기준은 하나로 둔다.

```text
backend
└─ app
```

코드에서는 `from app...` 형태를 쓴다.
VS Code, Pyright, pytest, Docker는 모두 `backend`를 import root로 보게 맞춘다.

새 폴더를 만들 때는 기본적으로 `__init__.py`를 만들지 않는다.
공개 export, package 초기화, plugin discovery처럼 파일이 실제 역할을 가질 때만 추가한다.
새 import 경로를 추가했으면 아래 명령으로 확인한다.

```bash
mise run check
```

Pyright만 빠르게 확인하려면 아래 명령을 쓴다.

```bash
pnpm api:typecheck
```

VS Code에서 빨간 줄이 남으면 설정 문제가 아니라 캐시일 수 있다.
이때는 `Python: Restart Language Server` 또는 `Developer: Reload Window`를 실행한다.
