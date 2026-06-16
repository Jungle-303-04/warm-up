# Docker Compose 사용법

이 문서는 현재 RepoLM 최소 구현의 `compose.yaml`을 이해하기 위한 설명이다.

핵심부터 말하면 `dockerfile:`과 `<<:`는 같은 기능이 아니다.

```yaml
build:
  context: .
  dockerfile: apps/web/Dockerfile
```

위 설정은 Docker에게 "이미지를 만들 때 이 Dockerfile을 사용해"라고 말한다.

```yaml
api:
  <<: *backend-service
```

위 설정은 YAML에게 "아까 저장해 둔 설정 묶음을 이 위치에 합쳐 넣어"라고 말한다.

즉 둘의 역할은 다르다.

```text
dockerfile: Docker 이미지 빌드에 사용할 파일을 지정한다.
<<: YAML 설정 객체를 현재 위치에 병합한다.
```

## Docker와 Docker Compose의 차이

Docker는 컨테이너 하나를 만들고 실행하는 도구다.

예를 들어 FastAPI 서버 하나를 직접 실행한다면 대략 이런 생각이다.

```text
backend Dockerfile로 image 만들기
-> image에서 container 실행하기
-> 8000번 port 열기
-> 환경변수 넣기
```

Docker Compose는 여러 컨테이너를 한 번에 묶어서 실행하는 도구다.

RepoLM은 혼자 돌아가는 프로그램이 아니다.

```text
web
api
worker-repo-sync
worker-code-index
worker-rag
worker-agent
worker-publish
postgres
redis
```

이 여러 실행 단위를 `compose.yaml` 하나에 적어두고 한 번에 올리는 것이 Docker Compose다.

```bash
docker compose up --build
```

## Compose 파일의 큰 구조

현재 `compose.yaml`은 크게 네 부분이다.

```yaml
name: repolm

x-backend-env: &backend-env
  ...

x-backend-service: &backend-service
  ...

services:
  ...

volumes:
  ...
```

각 역할은 다음과 같다.

```text
name: Docker Compose 프로젝트 이름
x-backend-env: 재사용할 backend 환경변수 묶음
x-backend-service: 재사용할 backend 서비스 설정 묶음
services: 실제 실행할 컨테이너 목록
volumes: Docker가 관리할 저장공간 목록
```

## `x-`로 시작하는 설정

Compose에서 `x-`로 시작하는 top-level key는 실행 대상이 아니다.

예를 들어 다음 설정은 컨테이너를 만들지 않는다.

```yaml
x-backend-env: &backend-env
  REPOLM_ENV: ${REPOLM_ENV:-local}
  DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://repolm:repolm@postgres:5432/repolm}
```

이것은 실행할 서비스가 아니라 재사용할 메모장이다.

Python식으로 비유하면 다음에 가깝다.

```python
backend_env = {
    "REPOLM_ENV": "local",
    "DATABASE_URL": "postgresql+asyncpg://repolm:repolm@postgres:5432/repolm",
}
```

`x-backend-env`라는 이름 자체는 Compose에서 특별한 기능을 실행하지 않는다.
다만 `x-` prefix를 쓰면 "이건 Compose 확장 필드이고 서비스가 아니다"라는 의미가 분명해진다.

## YAML anchor와 merge

다음 줄에서 `&backend-env`가 중요하다.

```yaml
x-backend-env: &backend-env
```

`&backend-env`는 이 설정 묶음에 이름표를 붙이는 문법이다.

```text
이 설정 묶음을 backend-env라는 이름으로 기억해둬.
```

나중에 다음처럼 꺼내 쓴다.

```yaml
environment:
  <<: *backend-env
```

각 기호의 의미는 이렇다.

```text
&backend-env: 저장할 때 붙이는 이름표
*backend-env: 저장된 설정을 다시 꺼내는 참조
<<: 꺼낸 설정을 현재 mapping 안에 병합
```

아래 두 코드는 의미가 거의 같다.

반복해서 직접 쓰는 방식:

```yaml
api:
  environment:
    REPOLM_ENV: local
    DATABASE_URL: postgresql+asyncpg://repolm:repolm@postgres:5432/repolm
    REDIS_URL: redis://redis:6379/0

worker-repo-sync:
  environment:
    REPOLM_ENV: local
    DATABASE_URL: postgresql+asyncpg://repolm:repolm@postgres:5432/repolm
    REDIS_URL: redis://redis:6379/0
```

anchor와 merge를 쓰는 방식:

```yaml
x-backend-env: &backend-env
  REPOLM_ENV: local
  DATABASE_URL: postgresql+asyncpg://repolm:repolm@postgres:5432/repolm
  REDIS_URL: redis://redis:6379/0

api:
  environment:
    <<: *backend-env

worker-repo-sync:
  environment:
    <<: *backend-env
```

반복이 줄어들고, 환경변수를 바꿔야 할 때 한 곳만 바꾸면 된다.

## `dockerfile:`은 무엇인가

다음 설정은 YAML merge가 아니다.

```yaml
web:
  build:
    context: .
    dockerfile: apps/web/Dockerfile
```

이 설정은 Docker 이미지 빌드 규칙이다.

```text
context: Docker build에 사용할 기준 폴더
dockerfile: 그 context 안에서 사용할 Dockerfile 경로
```

현재 web service는 루트 전체를 build context로 사용한다.

```yaml
context: .
```

그리고 실제 빌드 절차는 `apps/web/Dockerfile`에서 읽는다.

```yaml
dockerfile: apps/web/Dockerfile
```

이 말은 다음과 비슷하다.

```bash
docker build -f apps/web/Dockerfile .
```

반대로 backend는 이렇게 되어 있다.

```yaml
x-backend-service: &backend-service
  build:
    context: ./backend
```

여기에는 `dockerfile:`이 없다.
이 경우 Docker는 build context 안의 기본 파일인 `Dockerfile`을 찾는다.

```text
context가 ./backend
dockerfile을 따로 안 씀
-> ./backend/Dockerfile 사용
```

정리하면 다음과 같다.

```text
<<: 설정을 합치는 YAML 문법
dockerfile: 이미지 빌드에 사용할 Dockerfile 경로
```

## `image`와 `build`

다음 설정을 보자.

```yaml
image: repolm-api:local
build:
  context: ./backend
```

`build`는 이미지를 어떻게 만들지 정한다.

`image`는 만들어진 이미지에 어떤 이름을 붙일지 정한다.

```text
build: ./backend/Dockerfile로 image를 만들어
image: 그 image 이름은 repolm-api:local로 해
```

`image`만 있고 `build`가 없으면 Docker Hub 같은 registry에서 이미지를 가져온다.

```yaml
postgres:
  image: pgvector/pgvector:pg16
```

이 경우는 직접 빌드하지 않는다.

```text
pgvector/pgvector:pg16 이미지를 받아서 실행한다.
```

## 환경변수 기본값 문법

다음 문법을 자주 본다.

```yaml
REPOLM_ENV: ${REPOLM_ENV:-local}
```

의미는 다음과 같다.

```text
host 환경변수 REPOLM_ENV가 있으면 그 값을 사용한다.
없으면 local을 사용한다.
```

예를 들어 `.env`에 다음 값이 있으면:

```env
REPOLM_ENV=dev
```

Compose 안에서는 `dev`가 들어간다.

아무 값도 없으면 `local`이 들어간다.

빈 기본값도 가능하다.

```yaml
OPENAI_API_KEY: ${OPENAI_API_KEY:-}
```

이 뜻은 다음과 같다.

```text
OPENAI_API_KEY가 있으면 사용한다.
없으면 빈 문자열을 사용한다.
```

## Compose 내부 DNS와 service name

다음 DB URL을 보자.

```yaml
DATABASE_URL: postgresql+asyncpg://repolm:repolm@postgres:5432/repolm
```

여기서 `postgres`는 인터넷 도메인이 아니다.

Compose 안에 이런 service가 있다.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
```

같은 Compose 네트워크 안에서는 service 이름이 hostname처럼 동작한다.

즉 api 컨테이너 안에서:

```text
postgres:5432
```

라고 쓰면 `postgres` service 컨테이너의 5432번 포트로 연결된다.

주의할 점은 host와 container의 관점이 다르다는 것이다.

```text
내 Mac에서 DB 접속: localhost:5432
api 컨테이너에서 DB 접속: postgres:5432
```

그래서 backend의 `DATABASE_URL`에는 `localhost`가 아니라 `postgres`를 쓴다.

Redis도 같다.

```yaml
REDIS_URL: redis://redis:6379/0
```

여기서 앞의 `redis`는 service 이름이다.

## `ports`

다음 설정은 port 연결이다.

```yaml
ports:
  - "8000:8000"
```

왼쪽은 내 Mac의 포트다.
오른쪽은 컨테이너 내부 포트다.

```text
host:container
```

즉 다음 뜻이다.

```text
내 Mac localhost:8000으로 들어온 요청을
api 컨테이너 내부 8000번 포트로 보내라.
```

Postgres와 Redis는 이렇게 되어 있다.

```yaml
ports:
  - "127.0.0.1:5432:5432"
```

앞에 `127.0.0.1`을 붙이면 내 Mac 안에서만 접근 가능하다.
외부 네트워크에 DB port를 열지 않겠다는 뜻이다.

## `volumes`

Compose의 volume에는 자주 쓰는 두 종류가 있다.

```text
bind mount
named volume
```

### bind mount

다음은 bind mount다.

```yaml
volumes:
  - ./backend/app:/app/app
```

왼쪽은 내 Mac의 폴더다.
오른쪽은 컨테이너 안의 폴더다.

```text
host path:container path
```

의미는 다음과 같다.

```text
내 Mac의 ./backend/app 폴더를
컨테이너 안의 /app/app 폴더로 연결한다.
```

이렇게 하면 로컬에서 코드를 수정했을 때 컨테이너도 바로 변경된 코드를 본다.
개발 중 hot reload에 유용하다.

### named volume

다음은 named volume이다.

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

왼쪽 `postgres_data`는 로컬 경로가 아니다.
Docker가 관리하는 저장공간 이름이다.

오른쪽 `/var/lib/postgresql/data`는 컨테이너 안에서 Postgres가 DB 파일을 저장하는 위치다.

의미는 다음과 같다.

```text
Postgres 컨테이너의 DB 파일 저장 폴더를
Docker가 관리하는 postgres_data 저장공간에 연결한다.
```

컨테이너는 지우고 다시 만들 수 있다.
하지만 named volume은 따로 지우지 않으면 남아 있다.

```text
container 삭제
-> named volume 유지
-> 새 container가 같은 named volume 연결
-> DB 데이터 유지
```

아래 top-level `volumes`는 named volume 목록을 선언한다.

```yaml
volumes:
  postgres_data:
  redis_data:
  web_node_modules:
  web_app_node_modules:
  web_next:
```

### 왜 node_modules도 named volume으로 두는가

web service에는 이런 설정이 있다.

```yaml
volumes:
  - ./apps/web:/repo/apps/web
  - web_node_modules:/repo/node_modules
  - web_app_node_modules:/repo/apps/web/node_modules
  - web_next:/repo/apps/web/.next
```

첫 줄은 로컬 코드를 컨테이너에 연결한다.

```yaml
- ./apps/web:/repo/apps/web
```

그런데 이러면 컨테이너 이미지 안에 설치된 `node_modules`가 로컬 폴더 mount 때문에 가려질 수 있다.

그래서 `node_modules`와 `.next`는 named volume으로 따로 보존한다.

```text
소스코드: bind mount로 로컬 변경 반영
node_modules: named volume으로 컨테이너 의존성 보존
.next: named volume으로 Next.js dev cache 보존
```

## `depends_on`과 healthcheck

다음 설정은 api가 DB와 Redis를 기다리게 만든다.

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

중요한 점은 컨테이너가 "시작됨"과 서비스가 "사용 가능함"은 다르다는 것이다.

```text
컨테이너 시작됨: 프로세스가 켜짐
서비스 healthy: 실제로 접속 가능함
```

Postgres는 켜졌다고 바로 query를 받을 수 있는 것이 아니다.
초기화 시간이 필요하다.

그래서 healthcheck를 둔다.

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-repolm} -d ${POSTGRES_DB:-repolm}"]
```

이 명령이 성공해야 `postgres`는 healthy가 된다.

api도 healthcheck가 있다.

```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()\""]
```

api 컨테이너 내부에서 자기 자신의 `/health`를 호출한다.
성공하면 web이 시작될 수 있다.

## `command`

`command`는 이미지의 기본 실행 명령을 Compose에서 덮어쓴다.

api는 이렇게 실행된다.

```yaml
command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

의미는 다음과 같다.

```text
uvicorn으로 app.main 안의 app 객체를 0.0.0.0:8000에 띄운다.
코드 변경 시 reload한다.
```

worker는 같은 image를 쓰지만 command만 다르다.

```yaml
command: ["python", "-m", "app.workers.runner", "repo-sync"]
```

즉 같은 backend image에서:

```text
api는 uvicorn 실행
worker는 app.workers.runner 실행
```

이렇게 역할을 나눈다.

## 현재 RepoLM Compose 실행 순서

실제로는 대략 이런 순서로 이해하면 된다.

```text
1. postgres container 시작
2. redis container 시작
3. postgres healthcheck 성공
4. redis healthcheck 성공
5. api와 worker들이 backend image로 시작
6. api healthcheck 성공
7. web container 시작
```

worker들은 현재 실제 queue job을 처리하지 않고 heartbeat만 출력한다.
나중에 Redis queue를 붙이면 worker들이 job을 가져가 처리하게 된다.

## 자주 쓰는 명령

```bash
docker compose config
```

Compose 파일을 해석한 최종 설정을 출력한다.
anchor, merge, 환경변수 기본값이 적용된 결과를 볼 수 있다.

```bash
docker compose config --quiet
```

설정이 문법적으로 유효한지만 조용히 검사한다.

```bash
docker compose up --build
```

이미지를 build하고 모든 서비스를 실행한다.

```bash
docker compose up --build -d
```

백그라운드로 실행한다.

```bash
docker compose logs -f
```

모든 서비스 로그를 따라본다.

```bash
docker compose logs -f api
```

api 로그만 본다.

```bash
docker compose ps
```

서비스 상태와 port를 확인한다.

```bash
docker compose down
```

컨테이너와 네트워크를 내린다.
named volume은 기본적으로 삭제하지 않는다.

```bash
docker compose down -v
```

컨테이너, 네트워크와 함께 named volume도 삭제한다.
DB 데이터가 날아갈 수 있으므로 조심해서 쓴다.

## 헷갈리는 개념 요약

| 개념 | 의미 | 현재 예시 |
|---|---|---|
| `x-backend-env` | 실행되지 않는 재사용 설정 블록 | backend 환경변수 묶음 |
| `&backend-env` | 설정 묶음에 붙이는 이름표 | 저장할 때 사용 |
| `*backend-env` | 저장된 설정 묶음 참조 | 꺼낼 때 사용 |
| `<<:` | 참조한 설정을 현재 위치에 병합 | `environment`에 env 묶음 삽입 |
| `build.context` | Docker build 기준 폴더 | `./backend`, `.` |
| `build.dockerfile` | 사용할 Dockerfile 경로 | `apps/web/Dockerfile` |
| `image` | 사용할 image 이름 | `repolm-api:local`, `redis:7-alpine` |
| service name | Compose 내부 hostname | `postgres`, `redis`, `api` |
| bind mount | host 폴더를 container에 연결 | `./backend/app:/app/app` |
| named volume | Docker가 관리하는 저장공간 | `postgres_data` |
| healthcheck | 서비스 사용 가능 여부 검사 | `/health`, `pg_isready`, `redis-cli ping` |

## 지금 파일에서 가장 중요한 판단

현재 `compose.yaml`은 개발용이다.

개발용이라서 다음 설정이 들어간다.

```text
--reload
bind mount
host port 공개
node_modules cache volume
local 기본 환경변수
```

운영용으로 갈 때는 보통 다음이 달라진다.

```text
--reload 제거
bind mount 제거
secret 관리 강화
DB/Redis port 외부 공개 제거
restart policy 추가
production Dockerfile target 사용
```

그래서 이 파일은 "로컬에서 빠르게 개발하고 구조를 검증하기 위한 Compose"로 이해하면 된다.
