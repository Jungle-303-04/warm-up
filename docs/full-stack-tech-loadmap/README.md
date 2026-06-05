# Full Stack Tech Loadmap

출처: [원본 PDF 1쪽](./full-stack-tech-loadmap.pdf#page=1)

이 문서는 PDF에 있는 풀스택 기술 키워드를 팀원들과 같이 보기 위해 정리한 기술 사전이다.
목표는 "이걸 외우자"가 아니라, 각 기술이 어떤 문제를 풀려고 생겼고 언제 쓰이는지 한 번에 훑는 것이다.

읽을 때는 정의를 먼저 외우기보다, 기술 이름 뒤에 숨어 있는 질문을 찾는 게 좋다.

```text
React는 무엇인가?       -> 화면을 어떻게 작게 나눠서 만들까?
REST는 무엇인가?        -> 클라이언트와 서버가 어떤 약속으로 대화할까?
Transaction은 무엇인가? -> 여러 DB 작업을 어떻게 한 번에 성공/실패시킬까?
Architecture는 무엇인가? -> 코드가 커졌을 때 어디에 무엇을 둘까?
```

그래서 이 문서는 각 키워드를 백과사전처럼 짧게 정의하는 데서 끝내지 않고, 실제 개발할 때 어떤 장면에서 등장하는지까지 같이 적었다. 팀원이 모르는 키워드를 만났을 때 "대충 이런 역할이구나"까지 잡고 다음 대화로 넘어갈 수 있게 하는 게 목적이다.

PDF에는 프론트엔드, 백엔드, 데이터 계층, 아키텍처, 언어 기초가 한 장의 트리로 들어 있다.
처음 볼 때는 모든 키워드가 동등하게 중요해 보이지만, 실제로는 아래처럼 큰 흐름으로 묶어서 이해하는 게 편하다.

```text
Full Stack Tech
├── Language Basics
│   ├── Language: TypeScript, Java, Python
│   ├── Paradigm: OOP, Functional Programming
│   ├── Error Handling
│   └── Test Framework
├── Frontend
│   ├── HTML/CSS/JavaScript/TypeScript
│   ├── Framework: React, Vue.js
│   ├── Rendering: CSR, SSR, SSG, ISR, RSC
│   ├── Component Design
│   ├── State/Props
│   ├── Event
│   ├── Life Cycle
│   ├── Routing
│   ├── State Management: Redux Toolkit, Zustand, Pinia
│   ├── Test: Unit, Integration, E2E
│   ├── UI Framework: Tailwind, MUI, shadcn, Bootstrap
│   └── Accessibility: a11y
├── Backend
│   ├── Framework: FastAPI, Spring Boot, NestJS
│   ├── API: REST, gRPC, GraphQL
│   ├── API Design
│   ├── HTTP Error Handling: 3xx, 4xx, 5xx
│   ├── Authentication: Session, JWT, OAuth2, OIDC
│   ├── Realtime: WebSocket, SSE
│   ├── Security: HTTPS, OWASP Top 10, Rate Limit, CSRF/CORS
│   ├── Asynchronous Processing: Job Queue, RabbitMQ, Kafka
│   ├── Asynchronous Programming: Async, Event Loop
│   ├── Caching: Redis
│   ├── Logging
│   ├── Testing
│   └── Configuration
├── Data Layer
│   ├── RDBMS: PostgreSQL, MySQL
│   ├── SQL: CRUD, Join
│   ├── Data Modeling: ERD, PK, FK, Index, Normalization
│   ├── Transaction: Isolation, Lock, Deadlock
│   ├── Reliability: Idempotency, Retry, Timeout, Circuit Breaker
│   └── Scalability: Partition, Sharding
└── Architecture
    ├── MVC
    ├── Layered Architecture
    ├── Modular Monolith
    ├── Clean Architecture
    ├── Hexagonal Architecture
    ├── ADR
    ├── Microservices
    ├── Event-driven Architecture
    └── CQRS
```

## 문서 목록

- [01. Language Basics](./01-language-basics.md)
- [02. Frontend](./02-frontend.md)
- [03. Backend](./03-backend.md)
- [04. Data Layer](./04-data-layer.md)
- [05. Architecture](./05-architecture.md)
- [06. 한눈에 보는 선택 기준](./06-selection-guide.md)

## 키워드 링크

### Language Basics

- [Language Basics](./01-language-basics.md#language-basics)
- [Language](./01-language-basics.md#language)
- [TypeScript](./01-language-basics.md#typescript)
- [Java](./01-language-basics.md#java)
- [Python](./01-language-basics.md#python)
- [Paradigm](./01-language-basics.md#paradigm)
- [OOP](./01-language-basics.md#oop)
- [Functional Programming](./01-language-basics.md#functional-programming)
- [Error Handling](./01-language-basics.md#error-handling)
- [Test Framework](./01-language-basics.md#test-framework)

### Frontend

- [Frontend](./02-frontend.md#frontend)
- [HTML/CSS/JavaScript/TypeScript](./02-frontend.md#html-css-javascript-typescript)
- [Framework](./02-frontend.md#frontend-framework)
- [React](./02-frontend.md#react)
- [Vue.js](./02-frontend.md#vuejs)
- [Rendering](./02-frontend.md#rendering)
- [CSR](./02-frontend.md#csr)
- [SSR](./02-frontend.md#ssr)
- [SSG](./02-frontend.md#ssg)
- [ISR](./02-frontend.md#isr)
- [RSC](./02-frontend.md#rsc)
- [Component Design](./02-frontend.md#component-design)
- [State/Props](./02-frontend.md#state-props)
- [Event](./02-frontend.md#event)
- [Life Cycle](./02-frontend.md#life-cycle)
- [Routing](./02-frontend.md#routing)
- [State Management](./02-frontend.md#state-management)
- [Redux Toolkit](./02-frontend.md#redux-toolkit)
- [Zustand](./02-frontend.md#zustand)
- [Pinia](./02-frontend.md#pinia)
- [Unit, Integration, E2E](./02-frontend.md#frontend-testing)
- [Tailwind](./02-frontend.md#tailwind)
- [MUI](./02-frontend.md#mui)
- [shadcn](./02-frontend.md#shadcn)
- [Bootstrap](./02-frontend.md#bootstrap)
- [a11y](./02-frontend.md#a11y)

### Backend

- [Backend](./03-backend.md#backend)
- [FastAPI](./03-backend.md#fastapi)
- [Spring Boot](./03-backend.md#spring-boot)
- [NestJS](./03-backend.md#nestjs)
- [API](./03-backend.md#api)
- [REST](./03-backend.md#rest)
- [gRPC](./03-backend.md#grpc)
- [GraphQL](./03-backend.md#graphql)
- [API Design](./03-backend.md#api-design)
- [HTTP 3xx/4xx/5xx Error Handling](./03-backend.md#http-error-handling)
- [Authentication](./03-backend.md#authentication)
- [Session](./03-backend.md#session)
- [JWT](./03-backend.md#jwt)
- [OAuth2](./03-backend.md#oauth2)
- [OIDC](./03-backend.md#oidc)
- [Realtime](./03-backend.md#realtime)
- [WebSocket](./03-backend.md#websocket)
- [SSE](./03-backend.md#sse)
- [Security](./03-backend.md#security)
- [HTTPS](./03-backend.md#https)
- [OWASP Top 10](./03-backend.md#owasp-top-10)
- [Rate Limit](./03-backend.md#rate-limit)
- [CSRF/CORS](./03-backend.md#csrf-cors)
- [Asynchronous Processing](./03-backend.md#asynchronous-processing)
- [Job Queue](./03-backend.md#job-queue)
- [RabbitMQ](./03-backend.md#rabbitmq)
- [Kafka](./03-backend.md#kafka)
- [Asynchronous Programming](./03-backend.md#asynchronous-programming)
- [Async](./03-backend.md#async)
- [Event Loop](./03-backend.md#event-loop)
- [Caching](./03-backend.md#caching)
- [Redis](./03-backend.md#redis)
- [Logging](./03-backend.md#logging)
- [Testing](./03-backend.md#backend-testing)
- [Configuration](./03-backend.md#configuration)

### Data Layer

- [Data Layer](./04-data-layer.md#data-layer)
- [RDBMS](./04-data-layer.md#rdbms)
- [PostgreSQL](./04-data-layer.md#postgresql)
- [MySQL](./04-data-layer.md#mysql)
- [SQL](./04-data-layer.md#sql)
- [CRUD](./04-data-layer.md#crud)
- [Join](./04-data-layer.md#join)
- [Data Modeling](./04-data-layer.md#data-modeling)
- [ERD](./04-data-layer.md#erd)
- [Primary Key, Foreign Key, Index](./04-data-layer.md#primary-key-foreign-key-index)
- [Normalization](./04-data-layer.md#normalization)
- [Transaction](./04-data-layer.md#transaction)
- [Isolation](./04-data-layer.md#isolation)
- [Lock/Deadlock](./04-data-layer.md#lock-deadlock)
- [Reliability](./04-data-layer.md#reliability)
- [Idempotency](./04-data-layer.md#idempotency)
- [Retry](./04-data-layer.md#retry)
- [Timeout](./04-data-layer.md#timeout)
- [Circuit Breaker](./04-data-layer.md#circuit-breaker)
- [Scalability](./04-data-layer.md#scalability)
- [Partition](./04-data-layer.md#partition)
- [Sharding](./04-data-layer.md#sharding)

### Architecture

- [Architecture](./05-architecture.md#architecture)
- [MVC](./05-architecture.md#mvc)
- [Layered Architecture](./05-architecture.md#layered-architecture)
- [Modular Monolith](./05-architecture.md#modular-monolith)
- [Clean Architecture](./05-architecture.md#clean-architecture)
- [Hexagonal Architecture](./05-architecture.md#hexagonal-architecture)
- [ADR](./05-architecture.md#adr)
- [Microservices](./05-architecture.md#microservices)
- [Event-driven Architecture](./05-architecture.md#event-driven-architecture)
- [CQRS](./05-architecture.md#cqrs)

## 읽는 순서 추천

처음 읽을 때는 아래 순서가 제일 자연스럽다.

1. [Language Basics](./01-language-basics.md)로 기본 용어를 잡는다.
2. [Frontend](./02-frontend.md)에서 브라우저 쪽 앱이 어떻게 구성되는지 본다.
3. [Backend](./03-backend.md)에서 서버, API, 인증, 보안, 비동기 처리를 본다.
4. [Data Layer](./04-data-layer.md)에서 DB와 데이터 안정성을 본다.
5. [Architecture](./05-architecture.md)에서 코드와 시스템을 어떻게 나눌지 본다.
6. [선택 기준](./06-selection-guide.md)에서 비슷한 기술들을 비교한다.

## PDF 표기와 일반 표기

PDF에 적힌 표기와 실제로 더 많이 쓰는 표기가 조금 다른 항목이 있다.
문서에서는 일반적으로 많이 쓰는 표기를 기준으로 설명하고, 아래처럼 대응해서 보면 된다.

| PDF 표기 | 문서 표기 | 메모 |
| --- | --- | --- |
| Typescript | TypeScript | 공식 표기는 TypeScript |
| Javascript | JavaScript | 공식 표기는 JavaScript |
| Vuejs | Vue.js | 공식 표기는 Vue.js |
| Sprint Boot | Spring Boot | PDF 오타로 보이며, 일반적으로 Spring Boot |
| Rest | REST | Representational State Transfer |
| GRPC | gRPC | 공식 표기는 gRPC |
| CURD | CRUD | 일반적으로 Create, Read, Update, Delete 순서 |
| ARD | ADR | Architecture Decision Record |
| error handling | Error Handling | 에러 처리 |
| test framework | Test Framework | 테스트 실행/검증 도구 |
| api design | API Design | API 계약 설계 |
| Layered architecture | Layered Architecture | 계층형 아키텍처 |
| Modular monolith | Modular Monolith | 모듈러 모놀리스 |
| clean architecture | Clean Architecture | 클린 아키텍처 |
| hexagonal architecture | Hexagonal Architecture | 헥사고날 아키텍처 |
| event-driven architecture | Event-driven Architecture | 이벤트 기반 아키텍처 |
