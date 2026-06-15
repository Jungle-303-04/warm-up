# 파이썬 `@property` 정리

## 한 줄 정의

`@property`는 **메서드를 "속성처럼" 접근하게** 만드는 데코레이터다. 괄호 없이
`obj.x`로 호출되지만, 내부적으로는 함수가 실행된다.

```python
class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius

    @property
    def area(self) -> float:        # 메서드지만
        return 3.14159 * self.radius ** 2

c = Circle(2)
c.area        # 12.56...  ← 괄호 없이 "속성처럼" 접근 (실제로는 함수 실행)
c.area = 10   # AttributeError ← setter가 없으면 읽기 전용
```

## 왜 쓰는가

1. **계산되는 속성**: 저장하지 않고 그때그때 계산(`area`처럼).
2. **읽기 전용 보장**: setter를 안 만들면 외부에서 못 바꿈(불변/캡슐화).
3. **검증/지연 초기화**: 접근 시점에 조건 검사나 lazy 생성.
4. **API 안정성**: 처음엔 일반 속성이었다가 나중에 로직이 필요해지면, **호출부 수정 없이**
   property로 바꿀 수 있다. (자바의 getX()/setX() 보일러플레이트가 필요 없는 이유)
5. **인터페이스 정의**: Protocol/ABC에서 "이 타입은 이런 속성을 가진다"를 선언.

## 문법: getter / setter / deleter

```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius          # 관례상 내부값은 _밑줄

    @property
    def celsius(self) -> float:          # getter
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:   # setter (검증 추가 가능)
        if value < -273.15:
            raise ValueError("절대영도 미만 불가")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:       # 계산되는 읽기 전용 속성
        return self._celsius * 9 / 5 + 32

t = Temperature(25)
t.celsius        # 25      (getter)
t.celsius = 30   # setter (검증 통과)
t.fahrenheit     # 86.0    (계산)
```

## 이 프로젝트의 실제 사용 예

### 1) 인터페이스(포트)를 속성으로 선언 — `EmbeddingClient`

```python
class EmbeddingClient(Protocol):
    @property
    def model(self) -> str: ...
    @property
    def dimension(self) -> int: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
```

"이 포트를 구현하려면 `model`, `dimension` 속성과 메서드를 가져야 한다"는 계약이다.
구현체는 이를 단순 getter로 채운다:

```python
class DeterministicEmbeddingClient:
    def __init__(self, dimension: int = 1536) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension
```

> 왜 그냥 `self.dimension = dimension` 속성으로 안 하나? 포트가 `@property`로 정의돼 있어
> 인터페이스를 맞추고, 외부에서 **읽기 전용**으로 노출하기 위해서다.

### 2) 검증이 들어간 property — `SqlUnitOfWork.repo_rag`

가장 교과서적인 예다. "컨텍스트매니저 안에서만 유효한 속성"을 property로 가드한다:

```python
class SqlUnitOfWork:
    def __init__(self, session_factory) -> None:
        self._repo_rag = None            # 아직 없음

    @property
    def repo_rag(self) -> SqlRepoRagStore:
        if self._repo_rag is None:
            raise RuntimeError("UnitOfWork must be used within a context manager")
        return self._repo_rag            # with 블록 진입 후에만 생성됨

    def __enter__(self):
        self._repo_rag = SqlRepoRagStore(self.session_factory())
        return self
```

`uow.repo_rag`는 속성처럼 보이지만, **잘못된 시점 접근을 막는 로직**이 들어 있다.
일반 속성이면 `None`이 새어나가 엉뚱한 곳에서 터졌을 것이다.

## 일반 속성 vs property — 언제 무엇을

- **기본은 일반 속성**으로 시작해라. 파이썬은 자바처럼 처음부터 getter/setter를 만들지 않는다.
- **로직이 필요해지면**(계산·검증·읽기전용·지연생성) 그때 property로 바꾼다.
- 핵심 이점: `obj.x` 호출부는 **그대로 두고** 내부 구현만 property로 교체 가능.

```python
# 처음
class User:
    def __init__(self, name): self.name = name

# 나중에 정규화가 필요해짐 → 호출부(user.name)는 안 바뀜
class User:
    def __init__(self, name): self.name = name
    @property
    def name(self): return self._name
    @name.setter
    def name(self, value): self._name = value.strip().title()
```

## 자주 쓰는 변형: `functools.cached_property`

비싼 계산을 **한 번만** 하고 캐시한다(인스턴스에 저장). setter는 없다.

```python
from functools import cached_property

class Repo:
    @cached_property
    def file_count(self) -> int:
        return expensive_scan()   # 최초 접근 때 1회만 실행, 이후 캐시값 반환
```

## 흔한 함정

- **무한 재귀**: getter 안에서 `self.x`(같은 property)를 쓰면 무한 호출. 반드시 `self._x`처럼
  **다른 내부 변수**를 참조.
  ```python
  @property
  def x(self): return self.x   # ❌ 무한 재귀
  @property
  def x(self): return self._x  # ✅
  ```
- **setter 없으면 읽기 전용**: `obj.x = ...` 하면 `AttributeError`.
- **클래스에 정의해야 함**: property는 클래스 속성이다. 인스턴스에 동적으로 못 붙인다.
- **`__slots__`와 함께 쓸 때**: 백킹 필드(`_x`)를 slots에 넣어야 한다.
- **부수효과 주의**: 속성처럼 보이니, getter에 무거운 작업/외부호출을 숨기면 읽는 사람이 놀란다.
  비싸면 `cached_property`나 명시적 메서드(`fetch_x()`)가 낫다.

## 자바 getter/setter와의 비교

| 자바 | 파이썬 |
|------|--------|
| `private x` + `getX()`/`setX()` 항상 작성 | 일반 속성으로 시작, 필요할 때만 `@property` |
| 호출: `obj.getX()` | 호출: `obj.x` (구현이 메서드든 속성이든 동일) |
| 보일러플레이트 많음 | 필요한 곳만 최소한 |

요지: 파이썬은 "**일단 속성, 로직이 필요하면 property**"가 관용구다. 미리 getter/setter를
만드는 자바식 습관은 파이썬에선 불필요하다.
