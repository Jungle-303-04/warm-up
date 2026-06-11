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
| VS Code/Pylance (backend 폴더만 열 때) | `backend/.vscode/settings.json`의 `python.analysis.extraPaths`가 `${workspaceFolder}`를 본다 |
| Pyright (repo root) | `pyrightconfig.json`이 `backend`를 extra path로 둔다 |
| Pyright (backend root) | `backend/pyrightconfig.json`이 현재 폴더를 extra path로 둔다 |
| pytest | `backend/pyproject.toml`의 `pythonpath = ["."]`와 `cwd = backend` 기준이다 |
| Docker | `backend/Dockerfile`의 `WORKDIR /app`, Compose의 `PYTHONPATH=/app` 기준이다 |
| Debug attach | `.vscode/launch.json`이 로컬 `backend`를 컨테이너 `/app`에 매핑한다 |

## 새 폴더를 추가할 때

`backend/app` 아래 새 패키지는 `__init__.py`를 둔다.
이 파일은 런타임 동작보다 에디터, Pyright, pytest, Docker가 같은 package 경계를 보도록 만드는 표식이다.

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

repo root에서 Pylance/Pyright import 인식만 빠르게 확인:

```bash
pnpm api:typecheck
```

`backend` 폴더만 열었거나 그 기준으로 확인하고 싶으면 아래 명령을 쓴다.

```bash
cd backend
../node_modules/.bin/pyright --project pyrightconfig.json
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
