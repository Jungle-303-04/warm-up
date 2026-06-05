# 05. Architecture

출처: [원본 PDF 1쪽](./full-stack-tech-loadmap.pdf#page=1)

<a id="architecture"></a>
## Architecture

아키텍처는 코드를 어떤 구조로 나누고, 시스템을 어떤 책임 단위로 구성할지 정하는 것이다.  
좋은 아키텍처의 목표는 멋있는 그림을 그리는 것이 아니라, 변경과 운영을 견디는 구조를 만드는 것이다.

아키텍처를 볼 때 나는 아래 질문을 먼저 한다.

```text
어떤 부분이 자주 바뀌는가?
어떤 규칙은 오래 유지되어야 하는가?
어디까지가 UI이고 어디부터가 비즈니스 로직인가?
DB나 외부 API가 바뀌어도 핵심 로직이 버틸 수 있는가?
팀원이 코드를 찾기 쉬운가?
```

아키텍처는 처음부터 거창한 그림을 그리는 일이 아니다. 오히려 "나중에 덜 고생하려면 지금 어디에 선을 그어야 할까?"에 가깝다.  
MVC, Layered, Clean, Hexagonal, Microservices 같은 이름은 서로 경쟁하는 정답이라기보다 복잡도를 나누는 방식들이다. 프로젝트 규모와 팀 상황이 다르면 좋은 구조도 달라진다.

<a id="mvc"></a>
## MVC

MVC는 Model, View, Controller로 코드를 나누는 패턴이다.

```text
Model: 데이터와 비즈니스 규칙
View: 사용자에게 보이는 화면
Controller: 요청을 받아 Model과 View를 연결
```

웹 서버에서는 보통 Controller가 HTTP 요청을 받고, Model을 사용해서 데이터를 처리한 뒤, View나 JSON 응답을 반환한다.

MVC는 아키텍처를 처음 배울 때 가장 많이 만나는 이름이다.  
핵심은 "화면, 데이터, 요청 처리 로직을 한 덩어리에 섞지 말자"다. 다만 서비스가 커지면 MVC만으로는 부족해서 Service, Repository, Use Case 같은 더 세밀한 경계가 필요해진다.

아래 상황에서 많이 쓰인다.

- 전통적인 웹 애플리케이션
- 서버가 화면까지 렌더링하는 구조
- 역할을 단순하게 나눠 시작하고 싶을 때

MVC만으로는 큰 시스템의 복잡도를 모두 해결하기 어렵다.  
Controller에 로직이 너무 많이 들어가면 fat controller가 되고, Model에 모든 것이 들어가면 fat model이 된다.

<a id="layered-architecture"></a>
## Layered Architecture

계층형 아키텍처는 코드를 역할별 계층으로 나누는 구조다.

보통 아래처럼 나눈다.

```text
Controller Layer: HTTP 요청/응답
Service Layer: 비즈니스 로직
Repository Layer: DB 접근
Domain/Model Layer: 핵심 데이터와 규칙
```

Layered Architecture는 웹 API 서버에서 가장 현실적으로 자주 쓰는 기본 구조다.  
Controller는 HTTP를 알고, Service는 업무 규칙을 알고, Repository는 DB를 안다. 이렇게 나누면 "API 모양이 바뀌는 수정"과 "비즈니스 규칙이 바뀌는 수정"과 "DB 접근이 바뀌는 수정"을 서로 덜 건드리게 된다.

아래 상황에서 좋다.

- 웹 API 서버를 명확한 구조로 만들고 싶다.
- 라우터와 비즈니스 로직을 분리하고 싶다.
- DB 접근 코드를 한곳에 모으고 싶다.
- 팀원이 코드를 찾기 쉽게 만들고 싶다.

계층을 나눴다고 자동으로 좋은 구조가 되는 것은 아니다.  
Service가 모든 일을 다 하는 거대한 파일이 되지 않게 책임을 잘 나눠야 한다.

<a id="modular-monolith"></a>
## Modular Monolith

Modular Monolith는 하나의 애플리케이션으로 배포하지만 내부를 모듈 단위로 명확히 나누는 구조다.

예를 들어 하나의 서버 안에 auth, posts, comments, billing 같은 모듈을 둔다.

```text
app
├── auth
├── posts
├── comments
└── notifications
```

각 모듈은 자기 책임을 가지고, 다른 모듈과의 경계를 명확히 한다.

이 구조의 장점은 현실적이라는 점이다.  
처음부터 마이크로서비스로 쪼개면 배포, 통신, 데이터 일관성이 어려워지지만, 아무 경계 없는 모놀리스로 가면 코드가 금방 엉킨다. Modular Monolith는 하나로 배포하면서도 내부 경계를 연습할 수 있는 중간 지점이다.

아래 상황에서 좋다.

- 마이크로서비스는 아직 과하다.
- 하나의 서버로 배포하고 싶다.
- 하지만 코드 구조는 기능별로 나누고 싶다.
- 나중에 일부 모듈을 서비스로 분리할 가능성이 있다.

모듈 경계가 없으면 그냥 큰 monolith가 된다.  
모듈 간 의존 방향과 공개 API를 정해야 한다.

<a id="clean-architecture"></a>
## Clean Architecture

Clean Architecture는 핵심 비즈니스 로직을 외부 기술로부터 보호하려는 구조다.

핵심 아이디어는 의존성이 안쪽으로 향해야 한다는 것이다.

```text
외부: Web, DB, Framework
중간: Interface, Adapter
안쪽: Use Case, Entity, Domain Rule
```

DB, 프레임워크, 외부 API는 바뀔 수 있지만 핵심 규칙은 오래 유지되어야 한다.

Clean Architecture를 이해할 때 핵심은 "프레임워크가 주인공이 아니게 만들기"다.  
FastAPI, Spring Boot, PostgreSQL 같은 기술은 바뀔 수 있지만, 서비스의 핵심 규칙은 쉽게 바뀌면 안 된다. 그래서 핵심 로직을 안쪽에 두고 외부 기술은 바깥쪽 adapter로 다루려는 것이다.

아래 상황에서 좋다.

- 비즈니스 규칙이 중요하다.
- DB나 프레임워크 교체 가능성을 열어두고 싶다.
- 테스트 가능한 핵심 로직을 만들고 싶다.
- 장기 유지보수가 중요하다.

초기 작은 프로젝트에 너무 엄격하게 적용하면 파일과 인터페이스가 지나치게 많아질 수 있다.  
핵심은 "프레임워크 코드와 비즈니스 로직을 섞지 않는다"는 방향성이다.

<a id="hexagonal-architecture"></a>
## Hexagonal Architecture

Hexagonal Architecture는 Ports and Adapters Architecture라고도 부른다.  
시스템의 핵심 로직을 가운데 두고, 외부와의 연결을 port와 adapter로 분리한다.

```text
Inbound Adapter: HTTP Controller, CLI, Message Consumer
Application Core: Use Case, Domain Logic
Outbound Port: Repository Interface, External API Interface
Outbound Adapter: DB Repository, API Client
```

핵심 로직은 "DB가 PostgreSQL인지 MySQL인지", "요청이 HTTP인지 메시지인지"를 몰라도 된다.

아래 상황에서 좋다.

- 외부 시스템 연동이 많다.
- 테스트에서 DB나 외부 API를 쉽게 대체하고 싶다.
- 핵심 로직을 입출력 방식과 분리하고 싶다.
- 장기적으로 구조를 탄탄하게 가져가고 싶다.

### Clean Architecture와 차이

둘은 방향이 비슷하다.  
Clean Architecture는 계층과 의존성 방향을 강조하고, Hexagonal Architecture는 port/adapter를 통해 외부 세계와 내부 세계의 경계를 강조한다.

<a id="adr"></a>
## ADR

PDF에는 `ARD(Architecture Decision Record)`라고 적혀 있지만, 일반적으로는 `ADR(Architecture Decision Record)`라고 부른다.  
ADR은 중요한 기술적 의사결정을 기록하는 문서다.

예를 들어 아래 같은 결정을 기록한다.

```text
왜 PostgreSQL을 선택했는가?
왜 REST API를 사용했는가?
왜 Redis를 캐시로 도입했는가?
왜 마이크로서비스가 아니라 모듈러 모놀리스를 선택했는가?
```

ADR은 보통 배경, 결정, 대안, 결과를 적는다.

아래 상황에서 좋다.

- 팀원이 왜 이런 결정을 했는지 알아야 한다.
- 나중에 같은 논쟁을 반복하고 싶지 않다.
- 기술 선택의 맥락을 남기고 싶다.
- 프로젝트 기록에서 의사결정 과정을 보여주고 싶다.

### 예시 구조

```md
# ADR-001: PostgreSQL을 메인 DB로 선택

## Context
서비스는 관계형 데이터와 검색 기능이 필요하다.

## Decision
PostgreSQL을 사용한다.

## Alternatives
MySQL, MongoDB를 검토했다.

## Consequences
관계형 모델과 확장 기능을 활용할 수 있지만 PostgreSQL 운영 지식이 필요하다.
```

<a id="microservices"></a>
## Microservices

마이크로서비스는 하나의 큰 시스템을 여러 작은 서비스로 나누어 독립적으로 배포하고 운영하는 구조다.

예를 들어 하나의 서비스가 아니라 여러 서비스로 나눈다.

```text
auth-service
post-service
comment-service
notification-service
payment-service
```

각 서비스는 자기 DB와 API를 가질 수 있고, 서로 네트워크로 통신한다.

아래 상황에서 고려한다.

- 조직 규모가 크다.
- 서비스별로 독립 배포가 필요하다.
- 특정 기능만 따로 확장해야 한다.
- 장애 격리와 팀 경계가 중요하다.

마이크로서비스는 작은 프로젝트를 자동으로 좋게 만들지 않는다.  
네트워크 통신, 분산 트랜잭션, 서비스 discovery, observability, 배포 자동화, 데이터 일관성 문제가 생긴다.

요약하면 마이크로서비스는 "기술 구조"이기도 하지만 "조직 구조"와도 연결된 선택이다.

<a id="event-driven-architecture"></a>
## Event-driven Architecture

이벤트 기반 아키텍처는 시스템의 변화나 사건을 이벤트로 발행하고, 다른 부분이 그 이벤트를 구독해서 처리하는 구조다.

예를 들어 게시글이 작성되면 `PostCreated` 이벤트를 발행할 수 있다.

```text
Post Service: PostCreated 발행
Notification Service: 알림 전송
Search Service: 검색 인덱스 갱신
Analytics Service: 통계 반영
```

아래 상황에서 좋다.

- 한 행동 이후 여러 후속 작업이 필요하다.
- 서비스 간 결합도를 낮추고 싶다.
- 비동기 처리가 많다.
- 이벤트 로그나 스트리밍 처리가 필요하다.

이벤트 기반 구조는 흐름이 눈에 잘 안 보일 수 있다.  
이벤트 이름, payload, 재처리, 중복 처리, 순서 보장, 추적 로그를 잘 설계해야 한다.

<a id="cqrs"></a>
## CQRS

CQRS는 Command Query Responsibility Segregation의 약자다.  
쓰기 모델과 읽기 모델을 분리하는 패턴이다.

Command는 상태를 변경하는 요청이다.

```text
CreatePost
UpdatePost
DeletePost
```

Query는 데이터를 읽는 요청이다.

```text
GetPostDetail
ListPopularPosts
SearchPosts
```

CQRS는 이 둘을 서로 다른 모델이나 경로로 분리한다.

아래 상황에서 고려한다.

- 읽기와 쓰기의 요구사항이 매우 다르다.
- 읽기 성능을 위해 별도 view model이 필요하다.
- 이벤트 소싱과 함께 사용한다.
- 복잡한 도메인에서 command와 query 책임을 분리하고 싶다.

단순 CRUD 서비스에 CQRS를 적용하면 복잡도만 늘 수 있다.  
CQRS는 "읽기/쓰기 요구가 달라서 분리할 이유가 있을 때" 사용하는 것이 좋다.
