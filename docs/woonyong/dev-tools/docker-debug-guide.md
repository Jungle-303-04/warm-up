# Docker 컨테이너 디버그

디버그 개념이 아직 헷갈리면 먼저 [디버그 실행 이해 노트](./debugging-mental-model.md)를 본다.

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

가장 쉬운 방법은 VS Code의 Run and Debug에서 아래 구성을 바로 실행하는 것이다.

- `Debug FastAPI in Docker (local window)`
- `Debug Next.js in Docker (local window)`

이 구성은 `.vscode/tasks.json`의 Docker Compose task를 먼저 실행한 뒤 디버거를 attach한다.
이때 VS Code는 새 컨테이너 창을 열지 않고, 현재 로컬 프로젝트 창에서 breakpoint와 path mapping을 사용한다.

터미널에서 직접 띄우고 attach하고 싶으면 일반 Compose 파일에 `compose.debug.yaml`을 덧붙인다.

```bash
mise run compose:debug
```

FastAPI만 먼저 보고 싶으면 아래 명령을 쓴다.

```bash
mise run compose:debug:api
```

## FastAPI breakpoint

1. VS Code에서 breakpoint를 건다.
2. Run and Debug에서 `Debug FastAPI in Docker (local window)`를 선택한다.
3. 디버거가 붙으면 FastAPI 서버가 올라온다.
4. 브라우저나 curl로 `http://localhost:8000`에 요청한다.

VS Code는 `localhost:5678`로 붙고, 컨테이너의 `/app` 경로를 로컬 `backend` 폴더에 매핑한다.
FastAPI Docker debug는 breakpoint 안정성을 위해 `--reload`를 끄고 실행한다.
서버는 바로 올라오고, 디버거가 붙은 뒤 요청을 보내면 breakpoint에서 멈춘다.

API 요청은 Swagger UI, REST Client, curl 중 편한 것을 쓴다.
구체적인 요청 예시는 [API 테스트 방법](./api-testing-guide.md)을 따른다.

## Next.js breakpoint

1. Run and Debug에서 `Debug Next.js in Docker (local window)`를 선택한다.
2. 브라우저에서 `http://localhost:3000`을 연다.
3. 터미널로 직접 띄웠다면 기존 web 컨테이너를 debug compose 기준으로 다시 생성해야 `9229` 포트가 열린다.

Next.js 디버거는 `localhost:9229`로 붙는다.

## 새 창이 비어 보일 때

Docker 확장에서 `Attach Visual Studio Code`나 `컨테이너에 연결`을 누르면 VS Code가 컨테이너 안으로 원격 접속한 새 창을 연다.
이 창은 디버거 attach 창이 아니라 컨테이너 쉘/파일 탐색용 창이다.

그 창에서 `열린 폴더 없음`이 보이는 것은 정상이다.
컨테이너 안에서 폴더를 보고 싶다면 `폴더 열기`로 `/app`을 열 수 있지만, 이 프로젝트의 권장 디버그 방식은 아니다.

권장 방식:

1. 빈 컨테이너 창을 닫는다.
2. 로컬 프로젝트 창 `SW_AI-W15-warm-up`으로 돌아온다.
3. Run and Debug에서 `Debug FastAPI in Docker (local window)`를 실행한다.
4. 로컬 파일에 breakpoint를 걸고 API 요청을 보낸다.

즉, Docker 컨테이너에 VS Code를 직접 연결하는 것이 아니라, 로컬 VS Code가 `localhost:5678`의 `debugpy`에 붙는 구조다.

## 작업만 끝나고 멈춘 것처럼 보일 때

`Docker Compose: FastAPI Debug Up` task는 `docker compose up -d`를 실행한다.
`-d`는 detached 모드라서 컨테이너를 백그라운드로 띄우고 터미널 작업은 바로 끝난다.
따라서 아래 메시지는 실패가 아니라 정상이다.

```text
터미널이 작업에서 다시 사용됩니다.
```

Run and Debug에서 실행했다면 이 task가 끝난 뒤 VS Code가 `localhost:5678`에 attach한다.
만약 task만 직접 실행했다면 디버거는 붙지 않는다.
이때는 같은 로컬 프로젝트 창에서 `Attach FastAPI in Docker (local window)`를 실행하면 된다.

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
