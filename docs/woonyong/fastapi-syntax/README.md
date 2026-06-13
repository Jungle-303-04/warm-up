# FastAPI 문법 정리

이 문서는 특정 프로젝트에 묶이지 않고, FastAPI를 사용할 때 반복해서 참고할 수 있는 범용 문법과 실무 설정을 정리한다.

## 1. FastAPI 앱 생성

FastAPI 앱은 보통 `main.py`에서 만든다.

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    version="0.1.0",
    summary="Short API summary",
    license_info={"name": "MIT"},
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
```

`FastAPI(...)`는 API 서버 객체를 생성한다. 이 객체에 router, middleware, startup/shutdown 훅을 붙이면서 서버를 구성한다.

주요 옵션:

- `title`: Swagger UI와 OpenAPI에 표시되는 API 이름
- `version`: API 또는 서비스 버전
- `summary`: API 한 줄 요약
- `description`: API 상세 설명. Markdown 사용 가능
- `license_info`: API 라이선스 정보
- `contact`: API 담당자 또는 팀 정보
- `docs_url`: Swagger UI 문서 경로
- `redoc_url`: ReDoc 문서 경로
- `openapi_url`: OpenAPI JSON 스펙 경로
- `lifespan`: 서버 시작/종료 시 실행할 훅

예시:

```python
app = FastAPI(
    title="Task Manager API",
    version="1.2.0",
    summary="Task and project management API",
    description="API for managing users, projects, tasks, and comments.",
    contact={
        "name": "API Team",
        "email": "api@example.com",
    },
    license_info={
        "name": "MIT",
    },
)
```

## 2. API 문서 경로

FastAPI는 기본적으로 문서 페이지를 자동 생성한다.

기본 경로:

```text
/docs
/redoc
/openapi.json
```

실무에서는 API 문서 경로를 `/api/...` 아래로 옮기는 경우가 많다.

```python
app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
```

문서 페이지를 운영 환경에서 숨기고 싶으면 `None`으로 끌 수 있다.

```python
app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
```

단, `openapi_url=None`으로 끄면 Swagger UI와 ReDoc도 OpenAPI 스펙을 읽지 못한다.

## 3. Router 연결

`APIRouter`는 API 경로들을 묶는 객체다.

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

앱에는 `include_router()`로 붙인다.

```python
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
```

기능별로 router를 나누면 유지보수가 쉽다.

```text
app/
├── main.py
├── api/router.py
├── users/router.py
├── projects/router.py
└── tasks/router.py
```

조립 예시:

```python
from fastapi import APIRouter

from app.users.router import router as users_router
from app.projects.router import router as projects_router
from app.tasks.router import router as tasks_router

api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
```

그러면 실제 경로는 다음처럼 된다.

```text
/users
/projects
/tasks
```

## 4. Path Parameter

경로 안에 들어가는 값은 path parameter다.

```python
@router.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, int]:
    return {"item_id": item_id}
```

요청:

```text
GET /items/10
```

FastAPI는 `"10"`을 `int`로 변환해서 `item_id`에 넣는다. 변환할 수 없으면 자동으로 422 에러를 반환한다.

## 5. Query Parameter

경로에는 없지만 URL 뒤에 붙는 값은 query parameter다.

```python
@router.get("/items")
def list_items(skip: int = 0, limit: int = 20) -> dict[str, int]:
    return {"skip": skip, "limit": limit}
```

요청:

```text
GET /items?skip=20&limit=10
```

기본값이 있으면 선택값이고, 기본값이 없으면 필수값이다.

```python
@router.get("/search")
def search(q: str) -> dict[str, str]:
    return {"q": q}
```

이 경우 `q`가 없으면 422 에러가 난다.

## 6. Request Body와 Pydantic

JSON body는 Pydantic `BaseModel`로 받는다.

```python
from pydantic import BaseModel


class CreateItem(BaseModel):
    name: str
    price: int


@router.post("/items")
def create_item(payload: CreateItem) -> CreateItem:
    return payload
```

요청 body:

```json
{
  "name": "keyboard",
  "price": 100
}
```

`payload`는 단순 변수명이다. 꼭 payload라고 해야 하는 것은 아니지만, 요청 body 전체를 의미할 때 자주 쓴다.

```python
def create_item(payload: CreateItem):
    print(payload.name)
    print(payload.price)
```

FastAPI는 요청 JSON을 읽고 `CreateItem`으로 검증한 뒤 함수에 넣어준다. 타입이 맞지 않으면 자동으로 422 에러를 반환한다.

## 7. Response Model

응답 JSON 모양도 Pydantic 모델로 제한할 수 있다.

```python
class ItemResponse(BaseModel):
    id: int
    name: str


@router.post("/items", response_model=ItemResponse)
def create_item(payload: CreateItem) -> dict[str, object]:
    return {
        "id": 1,
        "name": payload.name,
        "secret": "hidden",
    }
```

`response_model`을 쓰면 응답에서 `ItemResponse`에 없는 필드는 제거된다. 위 예시에서 `secret`은 응답에 포함되지 않는다.

## 8. Depends

`Depends`는 의존성을 주입하는 문법이다.

```python
from fastapi import Depends


def get_current_user() -> str:
    return "user-1"


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)) -> dict[str, str]:
    return {"user_id": user_id}
```

흐름:

```text
1. 요청이 들어온다.
2. FastAPI가 get_current_user()를 먼저 실행한다.
3. 반환값을 user_id에 넣는다.
4. get_me()를 실행한다.
```

DB session도 보통 `Depends`로 받는다.

```python
def get_session():
    with Session(engine) as session:
        yield session


@router.post("/items")
def create_item(
    payload: CreateItem,
    session: Session = Depends(get_session),
):
    ...
```

`yield`를 쓰는 dependency는 요청 처리 후 정리 코드까지 실행할 수 있다. DB session을 닫는 데 자주 사용한다.

## 9. HTTPException

API 에러를 명확하게 반환하고 싶으면 `HTTPException`을 사용한다.

```python
from fastapi import HTTPException


@router.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, int]:
    if item_id <= 0:
        raise HTTPException(status_code=400, detail="item_id must be positive")

    return {"item_id": item_id}
```

반환:

```json
{
  "detail": "item_id must be positive"
}
```

실무에서는 service layer에서 발생한 `ValueError`, `DomainError` 등을 router에서 HTTP 에러로 바꿔주는 패턴을 많이 쓴다.

```python
@router.post("/items")
def create_item(payload: CreateItem):
    try:
        return service.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

## 10. API Version Prefix

API 버전 prefix는 경로에 버전을 넣는 방식이다.

```python
app.include_router(api_router, prefix="/api/v1")
```

그러면 모든 API가 `/api/v1` 아래로 들어간다.

```text
/api/v1/health
/api/v1/users
/api/v1/projects
```

언제 쓰는가?

- 외부 클라이언트가 이미 API를 사용 중일 때
- 응답 구조를 크게 바꿔야 할 때
- 기존 API를 바로 깨뜨리면 안 될 때
- v1과 v2를 전환 기간 동안 같이 운영해야 할 때

예:

```text
/api/v1/items/{id}
/api/v2/items/{id}
```

v1 응답:

```json
{
  "id": 1,
  "name": "keyboard"
}
```

v2 응답:

```json
{
  "data": {
    "id": 1,
    "name": "keyboard"
  }
}
```

버전 prefix는 “모든 코드를 버전마다 영원히 유지한다”는 뜻이 아니다. 기존 사용자가 새 버전으로 옮겨갈 시간을 주기 위한 장치다. 전환이 끝나면 오래된 버전은 deprecated 처리 후 제거한다.

MVP나 내부 도구는 처음부터 `/api/v1`을 안 써도 된다. 외부 사용자, 모바일 앱, 타 서비스 연동처럼 API 호환성이 중요해질 때 도입하는 편이 자연스럽다.

## 11. CORS

CORS는 브라우저가 다른 출처의 요청을 제한하는 보안 정책이다.

출처는 다음 조합으로 정해진다.

```text
scheme + host + port
```

예:

```text
프론트엔드: http://localhost:3000
백엔드:     http://localhost:8000
```

둘은 포트가 다르므로 서로 다른 출처다. 브라우저에서 프론트가 백엔드 API를 호출하려면 백엔드가 해당 출처를 허용해야 한다.

FastAPI 설정:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

옵션 의미:

- `allow_origins`: 허용할 프론트엔드 주소
- `allow_credentials`: cookie, Authorization header 같은 인증 정보를 허용할지
- `allow_methods`: 허용할 HTTP method
- `allow_headers`: 허용할 요청 header

주의:

```python
allow_origins=["*"]
```

는 개발 중에는 편하지만 운영에서는 위험할 수 있다. 특히 cookie 인증을 쓴다면 명시적인 origin 목록을 쓰는 편이 좋다.

## 12. Lifespan

`lifespan`은 서버 시작과 종료 시 실행할 코드를 정의한다.

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # startup
    print("server starting")
    yield
    # shutdown
    print("server stopping")


app = FastAPI(lifespan=lifespan)
```

흐름:

```text
1. 서버 시작
2. yield 위쪽 코드 실행
3. 서버가 요청 처리
4. 서버 종료
5. yield 아래쪽 코드 실행
```

시작 시점에 자주 하는 일:

- DB 연결 확인
- migration 상태 확인
- 외부 API 설정 확인
- cache/queue 연결 확인
- background scheduler 시작

종료 시점에 자주 하는 일:

- DB connection pool 정리
- queue connection 종료
- background task 종료
- 임시 파일 정리

중요한 점은 startup에서 너무 오래 걸리는 작업을 무조건 실행하면 서버가 늦게 뜬다는 것이다. 무거운 초기 작업은 background job으로 넘기고, lifespan에서는 필수 설정 검증 정도만 하는 것이 안전하다.

## 13. Middleware

Middleware는 모든 요청/응답 사이에 공통으로 끼어드는 처리다.

예:

- CORS
- request logging
- 인증 토큰 검사
- request id 생성
- 처리 시간 측정

간단한 middleware 예시:

```python
import time
from fastapi import Request


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(elapsed)
    return response
```

## 14. 기본 프로젝트 구조

작은 프로젝트:

```text
app/
├── main.py
├── schemas.py
├── router.py
└── service.py
```

기능이 늘어나는 프로젝트:

```text
app/
├── main.py
├── api/
│   └── router.py
├── users/
│   ├── router.py
│   ├── schemas.py
│   ├── service.py
│   └── repository.py
├── projects/
│   ├── router.py
│   ├── schemas.py
│   ├── service.py
│   └── repository.py
└── tasks/
    ├── router.py
    ├── schemas.py
    ├── service.py
    └── repository.py
```

실무에서는 기능 단위로 묶는 구조가 커질수록 유리하다. 기능 하나를 이해하려면 해당 폴더 안에서 router, schema, service, repository를 같이 볼 수 있기 때문이다.

## 15. 현재 프로젝트 적용 메모

이 프로젝트에서는 현재 다음 설정을 사용한다.

```text
docs_url="/api/docs"
redoc_url="/api/redoc"
openapi_url="/api/openapi.json"
license_info={"name": "MIT"}
lifespan 시작/종료 훅
```

아직 적용하지 않은 것:

```text
/api/v1 prefix
CORS middleware
```

이유:

- `/api/v1`은 API 경로 전체가 바뀌므로 프론트와 테스트가 같이 바뀌어야 한다.
- CORS는 브라우저 기반 프론트엔드가 백엔드를 직접 호출할 때 필요하다.

## 16. 같이 볼 문서

- [Python/FastAPI 어노테이션 정리](./annotations.md)
