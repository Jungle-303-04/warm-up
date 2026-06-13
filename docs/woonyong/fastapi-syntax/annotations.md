# Python/FastAPI 어노테이션 정리

이 문서는 코드에서 만나는 Python/FastAPI 어노테이션과 데코레이터를 누적 정리하는 공간이다.

앞으로 모르는 어노테이션을 질문하면 다음 원칙으로 정리한다.

- 채팅창에는 지금 이해할 수 있게 짧고 구체적으로 설명한다.
- 이 문서에는 다시 찾아볼 수 있게 정의, 동작 흐름, 사용 예시, 주의점을 추가한다.

## 어노테이션과 데코레이터의 차이

Python에서 보통 말하는 어노테이션은 타입 힌트를 뜻한다.

```python
def add(a: int, b: int) -> int:
    return a + b
```

- `a: int`: `a`는 정수라고 설명
- `b: int`: `b`는 정수라고 설명
- `-> int`: 반환값은 정수라고 설명

반면 `@something` 형태는 정확히는 데코레이터다.

```python
@router.get("/health")
def health():
    return {"status": "ok"}
```

데코레이터는 함수나 클래스를 감싸서 기능을 추가한다. FastAPI에서는 `@router.get`, `@router.post` 같은 데코레이터를 API 경로 등록에 사용한다.

## @asynccontextmanager

`@asynccontextmanager`는 async 함수 하나를 비동기 context manager로 바꿔주는 데코레이터다.

가져오는 위치:

```python
from contextlib import asynccontextmanager
```

기본 형태:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    # 시작할 때 실행
    yield
    # 끝날 때 실행
```

핵심은 `yield`를 기준으로 코드가 둘로 나뉜다는 점이다.

```text
yield 위쪽  -> context 시작 시 실행
yield       -> 실제 본문 실행 구간
yield 아래쪽 -> context 종료 시 실행
```

FastAPI의 `lifespan`에 사용하면 서버 생명주기와 연결된다.

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("서버 시작 전에 실행")
    yield
    print("서버 종료 전에 실행")


app = FastAPI(lifespan=lifespan)
```

실행 흐름:

```text
1. 서버 시작
2. "서버 시작 전에 실행" 실행
3. yield에서 FastAPI 서버가 요청을 처리하는 상태로 들어감
4. 서버 종료 신호
5. "서버 종료 전에 실행" 실행
```

실무에서 자주 쓰는 곳:

- DB connection pool 생성과 종료
- Redis/queue 연결 확인과 종료
- 외부 API 설정 검증
- background scheduler 시작과 중지
- 임시 디렉터리 생성과 정리

예시:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.db = create_database_pool()
    app.state.queue = create_queue_client()
    yield
    await app.state.queue.close()
    await app.state.db.close()
```

주의할 점:

- `yield`가 반드시 한 번 있어야 한다.
- startup 단계에서 너무 오래 걸리는 일을 하면 서버 시작이 늦어진다.
- 무거운 작업은 lifespan에서 직접 처리하기보다 background job으로 넘기는 편이 좋다.
- 종료 구간에서는 연결 종료, 파일 정리처럼 짧고 확실한 정리 작업을 넣는 것이 좋다.

## @router.get / @router.post

FastAPI의 `@router.get`, `@router.post`는 함수를 API endpoint로 등록하는 데코레이터다.

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}
```

의미:

```text
GET /items/{item_id} 요청이 오면 get_item 함수를 실행한다.
```

HTTP method에 따라 자주 쓰는 데코레이터:

- `@router.get`: 조회
- `@router.post`: 생성 또는 실행 요청
- `@router.put`: 전체 교체
- `@router.patch`: 일부 수정
- `@router.delete`: 삭제

## Depends(...)

`Depends`는 데코레이터는 아니지만 FastAPI에서 자주 만나는 의존성 주입 선언이다.

```python
from fastapi import Depends


def get_current_user() -> str:
    return "user-1"


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}
```

흐름:

```text
1. 요청이 들어온다.
2. FastAPI가 get_current_user를 먼저 실행한다.
3. 반환값을 user_id에 넣는다.
4. get_me를 실행한다.
```

DB session, 인증 사용자, service 객체 주입에 자주 사용한다.
