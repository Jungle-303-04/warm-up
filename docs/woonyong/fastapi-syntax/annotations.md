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

타입 힌트까지 같이 쓰려면 보통 `AsyncIterator`도 가져온다.

```python
from collections.abc import AsyncIterator
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

중요한 규칙:

- `async def` 함수에 붙인다.
- 함수 안에 `yield`가 있어야 한다.
- `yield`는 보통 한 번만 쓴다.
- `yield` 위쪽은 시작 처리다.
- `yield` 아래쪽은 종료 처리다.

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
- `yield`를 여러 번 쓰는 일반 generator처럼 사용하지 않는다.
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

## @field_validator

`@field_validator`는 Pydantic 모델에서 특정 필드 값을 검증하거나 정리할 때 쓰는 데코레이터다.

가져오는 위치:

```python
from pydantic import field_validator
```

기본 예시:

```python
from pydantic import BaseModel, field_validator


class RepoFile(BaseModel):
    path: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.strip()
        if not path:
            raise ValueError("파일 경로는 비어 있을 수 없습니다")
        return path
```

의미:

```text
RepoFile 객체를 만들 때 path 값을 검사한다.
검증에 성공하면 정리된 값을 반환한다.
검증에 실패하면 ValueError를 발생시킨다.
FastAPI 요청 body에서 실패하면 보통 422 validation error로 응답된다.
```

여러 필드를 한 함수로 검사할 수도 있다.

```python
class PipelineRequest(BaseModel):
    repository: str
    branch: str

    @field_validator("repository", "branch")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("값은 비어 있을 수 없습니다")
        return text
```

주의할 점:

- 필드 하나의 형식, 빈 값, 범위처럼 모델 자체가 책임질 수 있는 검증에 적합하다.
- DB 조회, GitHub API 호출처럼 외부 상태가 필요한 검증은 서비스 계층에서 처리하는 편이 좋다.
- validator는 값을 반환해야 한다. 반환값이 실제 모델 필드 값으로 들어간다.

## @classmethod

`@classmethod`는 메서드가 객체 인스턴스가 아니라 클래스 자체를 첫 번째 인자로 받게 하는 데코레이터다.

일반 인스턴스 메서드:

```python
class User:
    def hello(self):
        print(self)
```

`self`는 만들어진 객체 자신이다.

클래스 메서드:

```python
class User:
    @classmethod
    def create_guest(cls):
        return cls()
```

`cls`는 클래스 자신이다. 여기서는 `User`를 뜻한다.

Pydantic validator에서 자주 같이 쓰는 형태:

```python
@field_validator("path")
@classmethod
def validate_path(cls, value: str) -> str:
    ...
```

이렇게 쓰는 이유:

```text
validator는 특정 객체가 이미 만들어진 뒤 실행되는 메서드가 아니다.
객체를 만들기 전에 필드 값을 검사하는 클래스 수준 함수에 가깝다.
그래서 self 대신 cls를 받는 classmethod 형태로 둔다.
```

여기서 `cls`를 직접 쓰지 않더라도, Pydantic validator의 표준적인 형태라 같이 붙여두는 경우가 많다.

## @dataclass

`@dataclass`는 데이터를 담는 클래스를 짧게 만들 수 있게 해주는 Python 표준 라이브러리 데코레이터다.

가져오는 위치:

```python
from dataclasses import dataclass
```

기본 예시:

```python
@dataclass
class PipelineStage:
    id: str
    name: str
    purpose: str
```

위 코드는 Python이 자동으로 `__init__`, `__repr__`, `__eq__` 같은 기본 메서드를 만들어준다.

직접 쓰면 이런 코드를 작성해야 한다.

```python
class PipelineStage:
    def __init__(self, id: str, name: str, purpose: str) -> None:
        self.id = id
        self.name = name
        self.purpose = purpose
```

`@dataclass`를 쓰면 이렇게 바로 객체를 만들 수 있다.

```python
stage = PipelineStage(
    id="repo-sync",
    name="저장소 동기화",
    purpose="저장소 스냅샷을 만든다.",
)
```

필드 접근:

```python
print(stage.id)
print(stage.name)
print(stage.purpose)
```

즉 `@dataclass`는 “값을 담는 목적의 클래스”를 만들 때 코드 양을 줄여준다.

### @dataclass(frozen=True)

`frozen=True`는 객체를 만든 뒤 필드 값을 바꾸지 못하게 한다.

```python
@dataclass(frozen=True)
class PipelineStage:
    id: str
    name: str
    purpose: str
```

이렇게 만든 객체는 생성 후 수정할 수 없다.

```python
stage = PipelineStage(
    id="repo-sync",
    name="저장소 동기화",
    purpose="저장소 스냅샷을 만든다.",
)

stage.name = "다른 이름"  # 에러
```

왜 쓰는가?

- 설정값처럼 변하면 안 되는 데이터를 보호한다.
- 실수로 stage 정의를 바꾸는 일을 막는다.
- 값 객체처럼 안전하게 사용할 수 있다.

예를 들어 pipeline 단계 정의는 실행 중에 바뀌면 안 된다.

```python
PIPELINE_STAGES = (
    PipelineStage(id="repo-sync", name="저장소 동기화", purpose="..."),
    PipelineStage(id="code-index", name="코드 인덱싱", purpose="..."),
)
```

그래서 `PipelineStage`에 `frozen=True`를 붙이면 “이 단계 정의는 고정값이다”라는 의도가 코드에 드러난다.

### dataclass와 Pydantic BaseModel의 차이

`dataclass`는 Python 표준 라이브러리다. 가볍게 값을 담는 객체를 만들 때 좋다.

`BaseModel`은 Pydantic 기능이다. JSON 검증, 타입 변환, FastAPI 문서화가 필요할 때 좋다.

기준:

```text
내부에서만 쓰는 고정 설정/값 객체
-> dataclass

API 요청/응답 JSON 검증과 문서화
-> BaseModel
```

예:

```python
@dataclass(frozen=True)
class PipelineStage:
    id: str
    name: str
    purpose: str
```

이건 내부 stage 정의라 `dataclass`가 적절하다.

```python
class PipelineStageResponse(BaseModel):
    id: str
    name: str
    purpose: str
```

이건 API 응답 모델이라 `BaseModel`이 적절하다.
