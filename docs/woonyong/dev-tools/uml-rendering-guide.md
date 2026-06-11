# UML 렌더링 기준

이 문서는 클래스 UML을 Markdown 문서에 넣을 때 적용할 시각 기준을 정리한다.
현재 기준은 사용자의 VS Code 설정값인 `workbench.colorTheme = "One Dark Pro"`를 따른다.

## 기본 원칙

- Markdown에는 SVG 이미지를 먼저 제공하고, 렌더 원본을 함께 남긴다.
- 코드형 클래스 UML처럼 행간, 박스 폭, 라벨 색상을 세밀하게 제어해야 하는 경우 Graphviz DOT를 우선 사용한다.
- Mermaid 원본은 논리 구조 참조용으로 둘 수 있지만, 최종 SVG의 박스 좌표나 관계선 접점은 Mermaid 산출물을 직접 고쳐 만들지 않는다.
- SVG는 PNG보다 우선한다. PNG는 임시 확인용으로만 만들고 저장소에는 넣지 않는다.
- 배경, 클래스 블록, 텍스트, 관계선은 코드 테마와 같은 의미 체계로 색을 나눈다.
- 모든 관계선 화살표 머리는 같은 모양의 채워진 삼각형으로 통일한다.
- 텍스트가 박스 경계에서 잘리지 않도록 폰트 크기, 줄 높이, `foreignObject` overflow를 확인한다.
- 클래스 멤버, 메서드, 함수, 상수, 타입, 제네릭, 데코레이터, 생성자 호출은 실제 코드 문법과 비슷한 형태를 유지한다.
- 축약은 허용하되, 코드 구조가 사라지는 평면 나열형 축약은 금지한다.
- 상속, mixin, FK, 호출 흐름처럼 성격이 다른 관계선이 한 그림에서 섞여 읽기 어려워지면 SVG를 관심사별로 분리한다.

## One Dark Pro 색상 매핑

| UML 요소 | 의미 | 색상 |
|---|---|---|
| 전체 배경 | VS Code editor background | `#282c34` |
| 클래스 블록 배경 | VS Code editor/widget block | `#21252b` |
| 클래스 블록 테두리 | panel/border | `#3e4452` |
| 일반 텍스트 | 기본 foreground | `#abb2bf` |
| 클래스명, 자료형 | class/type token | `#e5c07b` |
| 필드명, 변수명 | variable/field token | `#e06c75` |
| 함수, 메서드 | function token | `#61afef` |
| 문자열, 테이블 참조 | string token | `#98c379` |
| 키워드, 제약 단어 | keyword token | `#c678dd` |
| 연산자, 기호 | operator token | `#56b6c2` |
| 숫자, cardinality | number/constant token | `#d19a66` |
| 주석성 라벨, stereotype | comment token | `#7f848e` |
| 관계선, 화살표 | diagram guide line | `#7f848e` |

## 의미별 칠하기 규칙

클래스 UML 멤버 라인은 실제 코드처럼 의미 단위로 색을 분리한다.
가능하면 원본 언어의 문법을 살린다.
단순 나열형 표기보다 코드에 가까운 표기가 읽기 쉽다.
축약은 허용하지만, 축약 후에도 실제 코드와 연결해서 읽을 수 있어야 한다.
즉, 필드명, 타입, 함수 호출, 문자열 literal, 핵심 키워드 인자는 남긴다.

이 규칙은 SQLAlchemy 모델에만 한정하지 않는다.
Python, TypeScript, Java, Kotlin, SQL 등 어떤 코드라도 UML 멤버 표기는 실제 코드와 같은 문법을 우선한다.

보존해야 하는 것:

- 필드명, 함수명, 클래스명
- 타입 힌트와 제네릭: `Mapped[int]`, `list[RepoFile]`, `Promise<User>`
- 함수/메서드 시그니처: 인자명, 인자 타입, 반환 타입
- 생성자와 함수 호출: `mapped_column(...)`, `ForeignKey("board.id")`
- 키워드 인자: `primary_key=True`, `nullable=False`
- 문자열 literal, 숫자 literal, enum/상수명
- 데코레이터와 annotation이 설계 이해에 중요하면 함께 표시

허용되는 축약:

- 상속/믹스인으로 이미 표현된 반복 필드는 하위 클래스에서 다시 쓰지 않는다.
- 긴 튜플/객체 래퍼는 핵심 호출만 남긴다.
- 반복되는 기본 인자는 설계 의미가 작으면 생략할 수 있다.
- 반복되는 모듈 접두나 네임스페이스는 의미가 명확하면 짧은 alias로 줄일 수 있다. 예: `datetime.utcnow` -> `utcnow`.
- 단, 생략한 내용이 리뷰에 중요하면 해석 메모에 남긴다.
- 멤버/메서드 라인은 기본적으로 한 줄로 유지한다. 줄바꿈으로 읽는 흐름이 깨질 정도라면 코드형 축약, SVG 자연 폭, 가로 스크롤, 다이어그램 분리를 순서대로 검토한다.

표준 별칭:

| UML 별칭 | 원본 코드 의미 |
|---|---|
| `Map[T]` | `Mapped[T]` |
| `col(...)` | `mapped_column(...)` |
| `FK("...")` | `ForeignKey("...")` |
| `PK=True` | `primary_key=True` |
| `AI=True` | `autoincrement=True` |
| `NULL=True` | `nullable=True` |
| `D=...` | `default=...` |
| `ON=...` | `onupdate=...` |
| `Check(...)` | `CheckConstraint(...)` |
| `table = "..."` | `__tablename__ = "..."` |
| `args = ...` | `__table_args__ = ...` |
| `Int`, `Str`, `DT`, `dt` | `Integer`, `String`, `DateTime`, `datetime` |
| `utcnow` | `datetime.utcnow` |
| `A|B` | `A | B` union type |

별칭은 문서 상단이나 해석 메모에 표로 남긴다.
한 다이어그램 안에서는 같은 원본 개념을 반드시 같은 별칭으로 쓴다.
기존 표준에 없는 반복 토큰을 더 축약해야 한다면, 같은 방향의 코드형 별칭을 만들고 이 표에 추가한 뒤 SVG를 다시 생성한다.

금지하는 축약:

- 실제 코드를 `타입 필드명 제약` 형태로 평평하게 나열하기
- 함수 호출을 `FK board.id`처럼 임의 문장으로 바꾸기
- 타입 정보를 `str?`, `list~T~`처럼 원본 언어와 다른 표기로 바꾸기
- 메서드 인자나 반환 타입을 이유 없이 제거하기

나쁜 축약 예:

```text
+int board_id PK FK board.id not null
```

이런 표기는 실제 코드의 `Mapped[...]`, `mapped_column(...)`, 함수 호출 구조를 잃기 때문에 쓰지 않는다.

가독성 있는 축약 예:

```text
board_id: Map[int] = col(FK("board.id"), PK=True)
```

`Integer`, `nullable=False`처럼 반복되는 인자는 생략하고, `Mapped`, `mapped_column`, `ForeignKey`, `primary_key`는 표준 별칭으로 줄였다.
필드명, 타입, 함수 호출, 문자열 구조는 남아 있어 실제 코드와 연결된다.
축약 여부는 줄 길이보다 이해도를 기준으로 정한다. 핵심 구조를 지우는 축약보다, 조금 길더라도 코드처럼 읽히는 표현을 우선한다.

권장 표현은 다음 의미로 나눈다.

| 조각 | 의미 | 색상 |
|---|---|---|
| `board_id` | 필드명 | `#e06c75` |
| `Map`, `int`, `Int` | 자료형 | `#e5c07b` |
| `col`, `FK`, `Check`, `utcnow` | 함수/호출 | `#61afef` |
| `"board.id"` | 문자열/테이블 참조 | `#98c379` |
| `PK`, `AI`, `NULL`, `D`, `ON`, `True` | 키워드/상수성 제약 | `#c678dd`, `#d19a66` |
| `:`, `=`, `(`, `)` | 연산자/기호 | `#56b6c2` |

union type은 한 줄 폭을 줄이기 위해 제네릭 내부에서 공백을 제거한다.

```text
tag: Map[str|None] = col(Str, NULL=True)
```

메서드는 실제 시그니처를 유지한다.

```text
to_chunk(self) -> RetrievalChunk
```

생성자나 서비스 메서드도 같은 원칙을 따른다.

```text
run(request: RepoRagSyncRequest) -> RepoRagSyncResponse
```

다른 언어도 같은 기준을 따른다.

```text
findById(id: UserId): Promise<User | null>
save(user: User): Result<Unit>
```

## 관계선과 화살표

- 관계선은 `#7f848e` 회색을 사용한다.
- 관계 라벨인 `board_id`, `user_id`는 필드명이므로 `#e06c75`를 사용한다.
- cardinality인 `1`, `0..1`, `0..*`는 숫자/상수이므로 `#d19a66`를 사용한다.
- cardinality가 화살표 머리나 박스 경계와 겹치면 `headlabel`/`taillabel` 대신 선 중간의 `xlabel`로 `1 -> 0..*`처럼 표시한다.
- 모든 marker는 같은 채워진 삼각형으로 통일한다.
- 빈 삼각형, 빈 다이아몬드, 작은 갈고리형 화살표가 섞이지 않게 SVG marker 정의를 후처리한다.

권장 marker 형태:

```svg
<marker markerWidth="18" markerHeight="14" orient="auto" markerUnits="userSpaceOnUse" viewBox="0 0 20 14">
  <path d="M 2 1 L 18 7 L 2 13 Z" fill="#7f848e" stroke="#7f848e" />
</marker>
```

시작점 화살표가 필요한 경우에는 좌우를 뒤집은 삼각형을 사용한다.

```svg
<path d="M 2 7 L 18 13 L 18 1 Z" fill="#7f848e" stroke="#7f848e" />
```

## 잘림 방지 기준

- 실제 문법을 최대한 보존해서 다이어그램이 넓어지면 폰트를 줄이지 말고 SVG 자연 폭 또는 가로 스크롤을 허용한다.
- 그래도 읽기 어렵다면 먼저 코드형 축약을 적용하고, 이후에도 복잡하면 다이어그램을 도메인/계층/관계별 SVG로 분리한다.
- 멤버 텍스트는 최소 13px, 권장 13-14px 전후로 유지한다.
- 클래스명은 최소 15px, 권장 15-16px 전후로 유지한다.
- stereotype은 최소 10px, 권장 10-12px 전후로 유지한다.
- `foreignObject`, 내부 `div`, `span`, `p`는 `overflow: visible`로 둔다.
- 멤버/메서드 `foreignObject`는 `white-space: nowrap`을 우선한다. 코드형 라인이 자동 줄바꿈되면 토큰 색상이 맞아도 코드처럼 보이지 않는다.
- SVG 루트가 `width="100%"`로 강제 축소되면 글자가 작아질 수 있다. 읽기용 SVG는 `viewBox`에 맞춘 자연 `width`, `height`를 명시한다.
- 박스 폭과 높이는 고정 상수보다 비율 기반으로 계산한다.
  - 기준 글자 크기 `font`를 정한다.
  - 행 높이 `rowHeight`는 `font * 1.15` 전후로 둔다.
  - 행 사이 간격 `rowGap`은 `font * 0.1` 전후로 둔다.
  - 좌우 패딩은 `font * 0.6`에서 `font * 0.8` 사이로 둔다.
  - 상하 패딩은 답답해 보이지 않게 `font * 0.6` 이상으로 둔다.
  - 박스 폭은 `가장 긴 코드 라인의 예상 폭 + 좌우 패딩`으로 잡고, 아주 조금의 여유만 둔다.
  - 박스 높이는 `헤더 높이 + 섹션 패딩 + rowHeight * 행 수 + rowGap * (행 수 - 1)`로 잡는다.
- 단, Mermaid CLI가 생성한 SVG에서는 박스 좌표, 노드 높이, edge 접점을 직접 재계산하지 않는다. Mermaid가 계산한 레이아웃을 덮어쓰면 관계선과 텍스트 위치가 쉽게 깨진다.
- Mermaid 기반 산출물에서 허용되는 후처리는 색상, marker 모양, SVG 자연 크기, 텍스트 overflow 정도로 제한한다.
- 박스 자체를 비율 기반으로 더 세밀하게 제어해야 하면 Mermaid 후처리가 아니라 Graphviz DOT, PlantUML, D2 같은 별도 렌더러를 선택하고, 그 도구의 규칙을 문서에 따로 남긴다.

## 렌더러 선택 기준

| 상황 | 우선 도구 | 이유 |
|---|---|---|
| 클래스 멤버를 코드처럼 한 줄로 보여줘야 함 | Graphviz DOT | HTML label로 토큰 색상, 행간, 박스 폭을 안정적으로 제어할 수 있다. |
| 표준 UML class notation이 중요함 | PlantUML | class diagram 문법과 UML 관계 표현이 가장 직접적이다. |
| 빠른 미리보기나 간단한 관계도 | Mermaid | Markdown에서 바로 읽기 쉽다. 단, 복잡한 SVG 좌표 후처리는 하지 않는다. |
| 앱/문서용 단순 구조도 | D2 | 선언형 레이아웃이 간단하다. 다만 class shape가 필드 라인을 메서드처럼 해석할 수 있으면 사용하지 않는다. |

Graphviz DOT를 사용할 때는 다음 규칙을 따른다.

- `.dot` 파일을 SVG의 실제 렌더 원본으로 저장한다.
- SVG는 `dot -Tsvg input.dot -o output.svg`로 재생성한다.
- 노드는 `shape=plain`과 HTML `TABLE` label을 사용해 박스 폭과 행간을 렌더러가 계산하게 한다.
- 코드 라인은 한 줄을 유지하고, 공백 정렬보다 실제 코드 구조와 토큰 색상을 우선한다.
- 멤버 라인은 한 셀 안에서 `<BR/>`로 이어 붙이지 말고, 가능하면 멤버별 `<TR><TD>...</TD></TR>` 행으로 나눈다. 그래야 위아래 여백이 실제 행 높이에 반영된다.
- 관계선은 `arrowhead=normal` 또는 `arrowtail=normal`의 채워진 삼각형을 사용한다.
- 상속/믹스인 관계와 FK/cardinality 관계는 기본적으로 별도 SVG로 나눈다. 두 종류를 한 장에 모두 넣어 선이 교차하면 정보가 맞아도 문서 품질은 실패로 본다.
- `headlabel`/`taillabel`이 화살표 머리와 겹치면 endpoint label을 고집하지 않는다. 관계도에서는 `xlabel="1 -> 0..*"`처럼 중앙 라벨을 우선 사용한다.
- 여러 edge가 cardinality 라벨 위를 지나가면 `raise-svg-cardinality-labels.py`로 라벨 텍스트를 SVG 마지막 레이어로 올린다.
- DOT 원본을 손으로 수정했다면 SVG를 다시 생성하고 Markdown 미리보기에서 잘림과 겹침을 확인한다.
- SVG 생성 후 Markdown 미리보기에서 아래를 확인한다.
  - 긴 필드 라인이 박스 오른쪽에서 잘리지 않는가?
  - edge label이 선이나 박스에 가려지지 않는가?
  - 화살표 머리가 같은 삼각형으로 보이는가?
  - 관계 라벨과 cardinality 색이 서로 구분되는가?
  - 전체 폭이 넓더라도 글자를 확대 없이 읽을 수 있는가?

## 문서 작성 방식

문서에는 SVG 이미지를 먼저 보여주고, 렌더 원본을 아래에 남긴다.
Graphviz DOT를 쓰는 경우 DOT 파일 링크와 재생성 명령을 함께 적고, Mermaid는 논리 구조 참조용으로만 남긴다.

````md
## 클래스 UML

![클래스 UML](./assets/class-uml.svg)

SVG는 Graphviz DOT 원본에서 생성한다.

```bash
dot -Tsvg docs/.../assets/class-uml.dot -o docs/.../assets/class-uml.svg
dot -Tsvg docs/.../assets/table-relations.dot -o docs/.../assets/table-relations.svg
python3 docs/woonyong/dev-tools/raise-svg-cardinality-labels.py docs/.../assets/table-relations.svg
```

## DOT 원본

- [class-uml.dot](./assets/class-uml.dot)

## 논리 원본

```mermaid
classDiagram
...
```
````

이 구조를 쓰면 Mermaid preview가 깨져도 SVG는 안정적으로 보이고, 나중에 다이어그램을 수정할 때 원본도 함께 유지된다.
