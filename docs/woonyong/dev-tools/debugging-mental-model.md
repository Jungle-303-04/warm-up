# 디버그 실행 이해 노트

## 지금 헷갈렸던 핵심

이번에 헷갈린 지점은 하나의 문제가 아니라 세 가지 개념이 한꺼번에 섞였기 때문이다.

```text
Docker 실행
VS Code 디버거 연결
브라우저 API 요청
```

이 셋은 서로 다르다.

Docker가 실행됐다고 해서 브라우저 화면이 자동으로 열리는 것은 아니다.
VS Code 디버거가 붙었다고 해서 API 요청이 자동으로 발생하는 것도 아니다.
브라우저에서 `localhost:8000`을 열었다고 해서 breakpoint가 자동으로 걸리는 것도 아니다.

## 한 줄 결론

이 프로젝트에서 FastAPI 디버그는 아래 구조다.

```text
VS Code 로컬 프로젝트 창
  -> Docker Compose로 api 컨테이너 실행
  -> api 컨테이너 안의 debugpy가 5678 포트를 연다
  -> VS Code 디버거가 localhost:5678에 붙는다
  -> 브라우저/curl/Swagger로 API 요청을 보내면 breakpoint에서 멈춘다
```

중요한 점은 VS Code를 컨테이너 안으로 직접 열 필요가 없다는 것이다.

## 정상 흐름

1. 로컬 VS Code/Cursor에서 `SW_AI-W15-warm-up` 폴더를 연다.
2. `backend/app/...` 파일에 breakpoint를 건다.
3. Run and Debug에서 `Debug FastAPI in Docker (local window)`를 실행한다.
4. VS Code task가 아래 명령을 실행한다.

```bash
docker compose -f compose.yaml -f compose.debug.yaml up -d --build api postgres redis
```

5. 터미널 작업은 끝난다.

```text
터미널이 작업에서 다시 사용됩니다.
```

이 메시지는 실패가 아니다.
`-d` 옵션 때문에 컨테이너가 백그라운드로 실행되고 터미널만 반환된 것이다.

6. VS Code 디버거가 `localhost:5678`에 attach한다.
7. 브라우저에서 `http://localhost:8000/docs`를 열거나 API 요청을 보낸다.
8. 요청이 breakpoint가 걸린 코드를 지나가면 VS Code가 멈춘다.

## 브라우저에서 무엇을 열어야 하나

FastAPI는 일반 웹 페이지가 아니라 API 서버다.

| 주소 | 의미 |
|---|---|
| `http://localhost:8000` | Swagger UI인 `/docs`로 이동한다 |
| `http://localhost:8000/docs` | API를 직접 눌러서 테스트하는 화면 |
| `http://localhost:8000/health` | 서버가 켜졌는지 확인 |
| `http://localhost:8000/pipeline` | 파이프라인 stage 목록 |
| `http://localhost:8000/pipeline/run` | POST 요청으로 파이프라인 실행 |

예전에 `{"detail":"Not Found"}`가 보였던 이유는 서버가 꺼져서가 아니다.
그때는 `/` 경로가 정의되어 있지 않았기 때문이다.
지금은 `/`를 `/docs`로 redirect하도록 바꿨다.

## VS Code에서 누르면 안 헷갈리는 것

디버그할 때는 Docker 확장의 `컨테이너에 연결`이나 `Attach Visual Studio Code`를 누르는 것이 아니다.

그 버튼을 누르면 VS Code가 컨테이너 안으로 들어간 새 창을 연다.
그 창에서 `열린 폴더 없음`이 보이는 것은 정상이다.
하지만 이 프로젝트의 디버그 방식은 그 창을 쓰지 않는다.

디버그할 때 누를 것:

```text
Run and Debug
-> Debug FastAPI in Docker (local window)
```

이미 컨테이너만 띄워져 있다면:

```text
Run and Debug
-> Attach FastAPI in Docker (local window)
```

## 파일별 역할

| 파일 | 역할 |
|---|---|
| `compose.yaml` | 일반 실행용 Docker Compose 설정 |
| `compose.debug.yaml` | 디버그용 override 설정. `debugpy`와 5678 포트를 연다 |
| `.vscode/tasks.json` | 디버그 전에 Docker Compose를 실행하는 VS Code task |
| `.vscode/launch.json` | VS Code가 어디에 attach할지 정하는 디버그 설정 |
| `.vscode/settings.json` | Python interpreter, pytest, 분석 경로 설정 |
| `backend/pyproject.toml` | backend package, pytest, ruff, 의존성 설정 |
| `pyrightconfig.json` | repo root에서 `app.*` import를 인식하게 하는 타입체크 설정 |
| `.pylintrc` | Pylint류 분석기가 `backend` import root를 찾도록 돕는 설정 |

## 디버그 설정이 하는 일

### `compose.debug.yaml`

API 컨테이너를 아래 방식으로 실행한다.

```text
/app/.venv/bin/python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

의미는 이렇다.

| 부분 | 의미 |
|---|---|
| `/app/.venv/bin/python` | 컨테이너 안의 backend 가상환경 Python을 사용 |
| `-Xfrozen_modules=off` | Python 디버거 breakpoint 경고를 줄임 |
| `-m debugpy` | Python 디버그 서버 실행 |
| `--listen 0.0.0.0:5678` | VS Code가 붙을 디버그 포트 열기 |
| `-m uvicorn app.main:app` | FastAPI 앱 실행 |
| `--port 8000` | API 서버 포트 |

### `.vscode/tasks.json`

Run and Debug를 누르기 전에 Docker를 먼저 띄운다.

```text
Docker Compose: FastAPI Debug Up
```

이 task는 컨테이너만 실행한다.
디버거 연결은 `.vscode/launch.json`이 한다.

### `.vscode/launch.json`

VS Code가 아래 주소에 붙는다.

```text
localhost:5678
```

그리고 컨테이너 안 경로와 로컬 경로를 연결한다.

```text
컨테이너: /app
로컬:     ${workspaceFolder}/backend
```

이 path mapping 덕분에 컨테이너 안에서 실행되는 코드가 로컬 파일의 breakpoint와 연결된다.

## 정상인지 확인하는 방법

서버가 켜졌는지:

```bash
curl http://localhost:8000/health
```

정상 응답:

```json
{"status":"ok"}
```

디버그 포트가 열렸는지:

```bash
python - <<'PY'
import socket

for port in (5678, 8000):
    s = socket.socket()
    s.settimeout(1)
    s.connect(("127.0.0.1", port))
    print(f"{port}: open")
    s.close()
PY
```

Docker 상태 확인:

```bash
docker compose -f compose.yaml -f compose.debug.yaml ps api postgres redis
```

## breakpoint 테스트 추천 위치

처음에는 아래 파일에 breakpoint를 걸면 좋다.

```text
backend/app/api/routes/pipeline.py
```

추천 줄:

```python
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
```

그 다음 Swagger UI에서 `POST /pipeline/run`에 `{}` 요청을 보내면 멈춰야 한다.

다음 단계로는 아래 파일을 보면 된다.

```text
backend/app/services/pipeline.py
```

여기서 실제 파이프라인 순서를 따라갈 수 있다.

## 증상별 해석

| 증상 | 의미 | 할 일 |
|---|---|---|
| `터미널이 작업에서 다시 사용됩니다` | Docker task가 정상 종료됨 | 실패 아님. 브라우저나 debugger를 확인 |
| `{"detail":"Not Found"}` | 서버는 켜졌지만 해당 API 경로가 없음 | `/docs`, `/health`, `/pipeline`으로 확인 |
| 새 VS Code 창에 `열린 폴더 없음` | 컨테이너에 직접 연결한 창 | 창을 닫고 로컬 프로젝트 창에서 Run and Debug 사용 |
| `/health`가 응답함 | API 서버는 실행 중 | 이제 breakpoint 걸고 API 요청 |
| `5678` 포트가 열림 | debugpy가 실행 중 | `Attach FastAPI in Docker (local window)` 사용 가능 |
| breakpoint가 안 멈춤 | 요청이 그 코드를 지나가지 않았거나 path mapping 문제 | `pipeline.py`의 route 함수부터 테스트 |

## 지금 기억할 것

처음에는 이 정도만 외우면 된다.

```text
Docker Compose = 서버를 띄운다
debugpy 5678 = VS Code가 붙는 통로다
localhost:8000 = API 요청을 보내는 주소다
Swagger /docs = API를 눈으로 눌러보는 화면이다
breakpoint = 요청이 그 줄을 지나갈 때 멈춘다
```

디버그는 버튼 하나가 모든 것을 해주는 마법이 아니다.
서버 실행, 디버거 attach, API 요청이 순서대로 맞물려야 멈춘다.
