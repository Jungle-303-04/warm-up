# 파이썬 데코레이터 정리

데코레이터 = "함수/클래스를 감싸서 동작을 더하거나 바꾸는 함수". `@something`은
`func = something(func)`의 문법 설탕이다. (★ = 이 프로젝트에서 실제 사용)

## 1. 내장 / 표준 라이브러리

### 클래스 안에서 쓰는 것
- **`@property`** ★ — 메서드를 속성처럼. (별도 문서 `python-property-guide.md`)
- **`@staticmethod`** — `self`/`cls` 없는 함수를 클래스에 묶기. 그냥 네임스페이스용.
- **`@classmethod`** — 첫 인자가 `cls`. 대체 생성자에 자주 씀.
  ```python
  class User:
      @classmethod
      def from_dict(cls, d): return cls(**d)   # User.from_dict({...})
  ```
- **`@abstractmethod`** ★ (`abc`) — 추상 메서드 강제. 우리 `LanguageChunker.build_chunks`.
  ```python
  class LanguageChunker(ABC):
      @abstractmethod
      def build_chunks(self, ctx): ...
  ```
- **`@functools.cached_property`** — 최초 접근 1회만 계산 후 캐시(인스턴스 저장).

### 클래스 자체에 붙이는 것
- **`@dataclass`** ★ (`dataclasses`) — `__init__`/`__repr__`/`__eq__` 자동 생성.
  우리 `ChunkDraft`, `FileContext`, 레코드들 전부. `@dataclass(slots=True)`로 메모리/속도↑.
- **`@typing.final`** — 상속/오버라이드 금지 표시(타입체커가 검사).
- **`@typing.runtime_checkable`** ★ — `Protocol`을 `isinstance()`로 검사 가능하게. 우리 `EmbeddingClient`.
- **`@enum.unique`** — Enum 값 중복 금지.

### 함수에 붙이는 것
- **`@functools.wraps`** ★(중요) — 데코레이터 만들 때 원본 함수의 이름/독스트링 보존. tenacity·우리가 만들었다 지운 데코레이터에서 필수였음.
- **`@functools.lru_cache` / `@functools.cache`** — 인자 기준 결과 캐시(메모이제이션). 순수함수에.
  ```python
  @lru_cache(maxsize=128)
  def fib(n): ...
  ```
  우리 `config.get_settings`도 `@lru_cache(maxsize=1)`로 싱글턴처럼 씀. ★
- **`@functools.singledispatch`** — 첫 인자 "타입별"로 다른 구현 디스패치(함수 오버로딩 흉내).
- **`@contextlib.contextmanager`** ★ — 제너레이터로 `with` 컨텍스트매니저 만들기. 우리 `db.session_scope`, `sql_store._session`.
  ```python
  @contextmanager
  def session_scope(factory):
      s = factory()
      try: yield s; s.commit()
      except: s.rollback(); raise
      finally: s.close()
  ```
- **`@typing.overload`** — 같은 함수의 여러 시그니처를 타입체커에 알림(런타임 영향 없음).
- **`@atexit.register`** — 프로그램 종료 시 실행.

## 2. 자주 쓰는 서드파티

- **FastAPI** ★ — `@app.get(...)`, `@router.post(...)`: 경로 등록. 우리 `api/router.py`.
- **Pydantic** ★ — `@field_validator`, `@model_validator`, `@computed_field`. 우리 `schemas.py`의 `@field_validator("text")`.
- **pytest** ★ — `@pytest.fixture`, `@pytest.mark.parametrize`, `@pytest.mark.skipif`. 우리 통합테스트 skipif.
- **tenacity** ★ — `@retry(...)`: 재시도. (우리는 임베딩에서 `tenacity.Retrying`을 함수형으로 씀)
- **click / typer** — `@app.command()`: CLI.
- **cachetools** — TTL/LRU 등 다양한 캐시 데코레이터.

## 3. 직접 만드는 데코레이터 (패턴 3가지)

### (a) 인자 없는 함수 데코레이터
```python
import functools, time

def timed(func):
    @functools.wraps(func)                 # ← 원본 메타데이터 보존(필수 습관)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__}: {time.perf_counter()-start:.3f}s")
    return wrapper

@timed
def work(): ...
```

### (b) 인자를 받는 데코레이터 (한 겹 더 감싼다)
```python
def retry(times=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times - 1:
                        raise
        return wrapper
    return decorator

@retry(times=5)
def flaky(): ...
```

### (c) 클래스 데코레이터
```python
def register(cls):
    REGISTRY[cls.__name__] = cls
    return cls

@register
class Foo: ...
```

> 우리가 한때 `@transactional`/`@component`를 직접 만들었다가 걷어낸 이유: 파이썬에선
> 트랜잭션은 **컨텍스트매니저**(`with`)가, DI는 **FastAPI Depends**가 더 관용적이라서다.
> 데코레이터는 "횡단 관심사(로깅·캐시·재시도)"에 쓰고, 흐름 제어는 `with`가 낫다.

## 핵심 규칙 한 줄

- 직접 만들면 **항상 `functools.wraps`**를 붙여라(이름/독스트링/시그니처 보존).
- 캐시는 `lru_cache`, 재시도는 `tenacity`, 컨텍스트는 `contextmanager` — **바퀴를 다시 만들지 마라.**
- 데코레이터는 "동작을 감싸는" 용도. 객체 조립/흐름 경계는 데코레이터보다 `with`·DI가 파이썬답다.

---

# 상세 (심화)

## `@functools.lru_cache` / `@functools.cache` — 자주 쓰나?

**예, 꽤 자주.** 순수 함수(같은 입력 → 같은 출력, 부수효과 없음)의 결과를 캐시한다.

```python
@lru_cache(maxsize=128)   # 최근 128개 캐시(LRU: 오래된 것부터 버림)
def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)
```

- `cache` = `lru_cache(maxsize=None)`(무제한, 3.9+).
- 조건: **인자가 해시 가능**해야 함(list/dict 인자엔 못 씀).
- 흔한 용도: 비싼 순수 계산 메모이제이션, 설정/상수 1회 생성(우리 `get_settings`가 `@lru_cache(maxsize=1)`),
  파싱 결과 캐시 등.
- 주의: **부수효과 있는 함수엔 금지**(DB 쓰기 등). 인스턴스 메서드에 걸면 self가 키에 포함돼 메모리 누수 위험.

## `@dataclass` — "보일러플레이트 제거"의 의미

기본 기능을 없애는 게 아니라, 손으로 쓸 **반복 코드를 자동 생성**한다. `@dataclass`는
`__init__`, `__repr__`, `__eq__`를 필드 선언만으로 만들어 준다.

```python
@dataclass(slots=True)        # slots=True → 메모리/속도 이득
class Point:
    x: int
    y: int
# __init__(self, x, y) / __repr__ / __eq__ 자동
```

## `@typing.runtime_checkable`

`Protocol`은 기본적으로 `isinstance()` 불가. 이 데코레이터를 붙이면 런타임에 "이 메서드들이
있는가"로 `isinstance` 검사가 가능해진다(메서드 **존재**만 보고 시그니처는 안 봄).

## `@functools.wraps`

데코레이터 wrapper가 원본 함수의 `__name__`·`__doc__`·시그니처를 덮어쓰는 걸 막아 **원본을 보존**.
직접 데코레이터를 만들 때 거의 필수.

---

## 비교 1 — Celery `@task`/`@shared_task` vs async

서로 다른 층위다.

- **async (`asyncio`)**: **한 프로세스의 이벤트 루프 안** 동시성. I/O 대기 중 다른 일을 처리(협력적
  멀티태스킹). 같은 프로세스라 재시작하면 사라지고, 머신 간 분산도 안 됨. "한 서버에서 느린 I/O를
  많이 동시에 처리".
- **Celery `@task`**: 작업을 **브로커(Redis/RabbitMQ)를 거쳐 별도 워커 프로세스/머신으로 분산**.
  내구성(재시작 생존)·재시도·스케줄·수평확장이 핵심. "무거운 백그라운드 잡을 떼어내 분산 처리".

요지: **async = 한 프로세스 안 동시성, Celery = 별도 워커로 작업 분산.** 둘은 배타적이지 않다
(Celery 워커 내부에서 async를 쓸 수도 있다). 우리 `poller.py`(DB 폴링 워커)가 사실상 Celery가
하는 일을 손으로 만든 축소판이다.

## 비교 2 — `@retry`(tenacity) vs 트랜잭션

완전히 다른 개념이다.

- **retry**: 실패하면 **다시 시도**. 일시적 오류(네트워크 끊김, 레이트리밋, 타임아웃)에 대응.
- **트랜잭션**: 여러 DB 작업을 **all-or-nothing**(원자성). 성공이면 commit, 실패면 rollback.

retry는 "다시 해본다", 트랜잭션은 "전부 되거나 전부 안 된다". 둘을 합칠 수도 있다(트랜잭션 전체를
retry로 감싸기 — 단, 재시도 시 트랜잭션을 새로 열어야 한다). 우리 임베딩 호출엔 retry,
sync DB 작업엔 UnitOfWork(트랜잭션)를 따로 쓴다.

## 비교 3 — `@login_required` / `@cached`(cachetools), 지금 코드에 쓸 수 있나?

- **`@login_required`**: Django/Flask 전용. 우리는 **FastAPI**라 인증을 데코레이터가 아니라
  **`Depends(get_current_user)`** 의존성으로 건다. 게다가 아직 인증 자체가 없다(로드맵 Phase 3).
  → 지금은 못 쓰고, 도입해도 형태는 데코레이터가 아니라 Depends가 된다.
- **`@cached`(cachetools, TTL 캐시)**: **쓸 수 있다.** 예: 저장소 resolve 결과나 검색 결과를 짧은
  TTL로 캐시. 단 stale(낡은 값) 위험이 있어 신중히. 우리의 "재임베딩 스킵"은 캐시보다 `chunk_hash`로
  DB에서 거르는 게 정석이라, cachetools는 "조회 핫패스"에 한정해 쓰는 게 맞다.
