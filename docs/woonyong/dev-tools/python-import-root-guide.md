# Python import root 기준

## 기준

RepoPilot backend의 Python import root는 `backend`다.

```text
backend
├─ app
└─ tests
```

코드는 항상 `app` package를 기준으로 import한다.

```python
from app.services.pipeline import PipelineService
from app.schemas.pipeline import PipelineRequest
```

아래 형태는 쓰지 않는다.

```python
from backend.app.services.pipeline import PipelineService
from services.pipeline import PipelineService
```

## 도구별 같은 기준

| 도구 | 기준 |
|---|---|
| VS Code/Pylance | `.vscode/settings.json`의 `python.analysis.extraPaths`가 `${workspaceFolder}/backend`를 본다 |
| Pyright | `pyrightconfig.json`의 execution root가 `backend`다 |
| pytest | `backend/pyproject.toml`의 `pythonpath = ["."]`와 `cwd = backend` 기준이다 |
| Docker | `backend/Dockerfile`의 `WORKDIR /app`, Compose의 `PYTHONPATH=/app` 기준이다 |
| Debug attach | `.vscode/launch.json`이 로컬 `backend`를 컨테이너 `/app`에 매핑한다 |

## 새 폴더를 추가할 때

`backend/app` 아래 새 폴더는 기본적으로 namespace package로 둔다.
`__init__.py`는 공개 export, package 초기화, plugin discovery처럼 파일 자체에 역할이 있을 때만 만든다.

```text
backend/app/features/service.py
```

그리고 import는 아래처럼 쓴다.

```python
from app.features.service import FeatureService
```

## 확인 명령

전체 확인:

```bash
mise run check
```

Pylance/Pyright import 인식만 빠르게 확인:

```bash
pnpm api:typecheck
```

Docker debug import 확인:

```bash
docker compose -f compose.yaml -f compose.debug.yaml run --rm --no-deps api \
  python -c "import debugpy; import app.pipeline; print('ok')"
```

## 빨간 줄이 남을 때

설정을 바꾼 직후 VS Code가 이전 분석 결과를 들고 있을 수 있다.

1. `Python: Restart Language Server`
2. 그래도 남으면 `Developer: Reload Window`
3. 이후 `pnpm api:typecheck`로 실제 Pyright 결과를 확인한다.
