# 03. Backend

출처: [원본 PDF 1쪽](./full-stack-tech-loadmap.pdf#page=1)

<a id="backend"></a>
## Backend

백엔드는 사용자가 직접 보지는 않지만 서비스의 핵심 로직과 데이터를 처리하는 영역이다.  
프론트엔드가 화면과 사용자 상호작용을 담당한다면, 백엔드는 API, 인증, 데이터 저장, 비즈니스 규칙, 보안, 외부 서비스 연동을 담당한다.

백엔드의 기본 흐름은 대략 이렇다.

```text
클라이언트 요청
-> 인증/권한 확인
-> 입력 검증
-> 비즈니스 로직 실행
-> DB 또는 외부 API 호출
-> 응답 반환
```

백엔드를 이해할 때는 "서버가 뭔가를 계산한다" 정도로 보면 너무 좁다. 백엔드는 약속을 지키는 쪽에 더 가깝다.  
누가 요청했는지 확인하고, 요청이 올바른지 판단하고, 데이터가 망가지지 않게 처리하고, 실패했을 때 적절히 알려준다. API, 인증, 보안, 비동기, 캐시 같은 키워드는 전부 이 약속을 안정적으로 지키기 위한 도구다.

<a id="fastapi"></a>
## FastAPI

FastAPI는 Python 기반의 웹 API 프레임워크다.  
이름처럼 빠른 개발 속도와 빠른 실행 성능을 목표로 한다.

FastAPI는 HTTP API를 쉽게 만들 수 있게 해준다.

```py
from fastapi import FastAPI

app = FastAPI()

@app.get("/posts")
def list_posts():
    return {"data": []}
```

타입 힌트와 Pydantic을 활용해서 요청/응답 검증과 API 문서 생성을 자동화한다.

아래 상황에서 좋다.

- Python으로 API 서버를 빠르게 만들고 싶다.
- AI, 데이터 처리, 자동화 라이브러리와 자연스럽게 연결하고 싶다.
- OpenAPI 문서가 자동으로 필요하다.
- 비동기 처리를 활용하고 싶다.

FastAPI 자체가 모든 구조를 정해주지는 않는다.  
프로젝트가 커질수록 라우터, 서비스, 저장소, 설정, 테스트 구조를 직접 잘 나눠야 한다.

<a id="spring-boot"></a>
## Spring Boot

PDF에는 `Sprint Boot`라고 적혀 있지만, 일반적으로는 `Spring Boot`를 의미한다.  
Spring Boot는 Java/Kotlin 기반의 백엔드 프레임워크다.

Spring Boot는 Spring 생태계를 쉽게 사용할 수 있게 해준다.  
웹 API, DB 연동, 보안, 트랜잭션, 설정, 테스트 등 백엔드에 필요한 많은 기능을 제공한다.

아래 상황에서 많이 쓰인다.

- 안정적인 대규모 백엔드 시스템을 만든다.
- 기업 환경에서 오래 운영할 서비스를 만든다.
- Java/Kotlin 생태계를 사용한다.
- 인증, 트랜잭션, DB 연동 같은 서버 기능을 탄탄하게 구성하고 싶다.

초기 학습량이 많다.  
하지만 구조가 잘 잡히면 큰 시스템에서 유지보수성이 좋다.

<a id="nestjs"></a>
## NestJS

NestJS는 Node.js 기반의 백엔드 프레임워크이고 TypeScript를 사용한다.  
구조적으로는 Angular나 Spring과 비슷하게 module, controller, service 개념을 사용한다.

NestJS는 TypeScript로 체계적인 서버를 만들 수 있게 해준다.

```ts
@Controller("posts")
export class PostsController {
  @Get()
  findAll() {
    return [];
  }
}
```

아래 상황에서 좋다.

- 프론트와 백엔드를 모두 TypeScript로 통일하고 싶다.
- Node.js 생태계를 쓰고 싶다.
- 구조화된 백엔드 프레임워크가 필요하다.
- REST, GraphQL, WebSocket 등을 함께 다루고 싶다.

Express처럼 가볍게 시작하는 방식보다 구조가 많다.  
작은 프로젝트에서는 다소 무겁게 느껴질 수 있지만, 팀 프로젝트에서는 일관된 구조가 장점이 된다.

<a id="api"></a>
## API

API는 Application Programming Interface의 약자다.  
소프트웨어끼리 서로 요청하고 응답하기 위한 약속이다.

웹 서비스에서 API는 보통 프론트엔드와 백엔드가 대화하는 통로다.

```text
프론트엔드: 게시글 목록 주세요.
백엔드 API: 여기 게시글 목록 JSON입니다.
```

API 방식에는 REST, gRPC, GraphQL 등이 있다.

세 방식은 같은 "API"라는 이름 아래에 있지만 감각이 다르다. REST는 웹에서 리소스를 다루는 표준적인 대화법에 가깝고, gRPC는 서버끼리 함수를 호출하는 계약에 가깝고, GraphQL은 클라이언트가 필요한 데이터 모양을 직접 고르는 방식에 가깝다.

```text
REST: /posts/1 주세요.
gRPC: PostService.GetPost(1)을 실행해주세요.
GraphQL: post의 title과 comments.author.name만 주세요.
```

<a id="rest"></a>
## REST

REST는 리소스 중심의 API 설계 방식이다.  
리소스는 사용자, 게시글, 댓글, 주문, 파일처럼 이름 붙일 수 있는 데이터 단위를 말한다.

REST는 HTTP 메서드와 URL을 조합해서 리소스를 다룬다.

```text
GET    /posts       게시글 목록 조회
POST   /posts       게시글 생성
GET    /posts/1     게시글 상세 조회
PATCH  /posts/1     게시글 수정
DELETE /posts/1     게시글 삭제
```

아래 상황에서 좋다.

- 리소스 중심의 CRUD API가 많다.
- 웹 표준 HTTP를 자연스럽게 쓰고 싶다.
- 프론트엔드와 백엔드가 쉽게 이해할 수 있는 API가 필요하다.
- OpenAPI/Swagger 문서화를 활용하고 싶다.

모든 기능을 REST답게 만들려고 억지로 끼워 맞출 필요는 없다.  
예를 들어 "요약 생성", "결제 승인", "비밀번호 재설정" 같은 작업은 `POST /posts/1/summarize`처럼 action endpoint를 두는 경우도 있다.

<a id="grpc"></a>
## gRPC

gRPC는 Google이 만든 고성능 RPC 프레임워크다.  
HTTP/2와 Protocol Buffers를 사용해서 서버끼리 빠르고 명확하게 통신할 수 있게 해준다.

REST가 리소스 중심이라면, gRPC는 함수 호출에 가깝다.

```text
PostService.GetPost(id)
UserService.CreateUser(input)
PaymentService.ApprovePayment(request)
```

데이터 형식은 `.proto` 파일로 정의한다.

아래 상황에서 많이 쓰인다.

- 서버와 서버 사이 통신이 많다.
- 성능과 통신 효율이 중요하다.
- 마이크로서비스 간 계약을 명확히 하고 싶다.
- 스트리밍 통신이 필요하다.

브라우저에서 직접 쓰기에는 REST보다 불편하다.  
gRPC-Web이나 gateway가 필요할 수 있다. 그래서 일반 웹 프론트엔드와 백엔드 사이에는 REST나 GraphQL이 더 흔하고, gRPC는 내부 서비스 통신에 많이 쓰인다.

<a id="graphql"></a>
## GraphQL

GraphQL은 클라이언트가 필요한 데이터 모양을 직접 요청할 수 있는 API 방식이다.

REST에서는 여러 API를 여러 번 호출해야 할 수 있다.

```text
GET /posts/1
GET /posts/1/comments
GET /users/3
```

GraphQL에서는 한 번의 query로 필요한 구조를 요청할 수 있다.

```graphql
query {
  post(id: 1) {
    title
    comments {
      content
      author {
        name
      }
    }
  }
}
```

아래 상황에서 좋다.

- 클라이언트마다 필요한 데이터 모양이 다르다.
- 모바일, 웹, 관리자 페이지가 같은 API를 다르게 사용한다.
- 중첩된 데이터를 효율적으로 가져오고 싶다.
- API 응답 필드를 클라이언트가 세밀하게 제어하고 싶다.

GraphQL은 도입하면 resolver, schema, 권한, 캐싱, N+1 문제를 신경 써야 한다.  
단순 CRUD 서비스에는 REST보다 복잡할 수 있다.

<a id="api-design"></a>
## API Design

API 디자인은 API를 어떻게 이름 짓고, 어떤 응답을 주고, 에러를 어떻게 표현할지 정하는 것이다.

좋은 API는 예측 가능해야 한다.

```text
GET /users
GET /users/{id}
GET /users/{id}/posts
```

응답도 일관되어야 한다.

```json
{
  "data": {
    "id": 1,
    "name": "Kim"
  }
}
```

API는 프론트엔드와 백엔드의 계약이다.  
처음에는 아무렇게나 만들어도 동작할 수 있지만, 기능이 늘어나면 일관성 없는 API가 큰 비용이 된다.

- URL은 명사를 중심으로 만든다.
- HTTP 메서드 의미를 지킨다.
- 상태 코드를 적절히 사용한다.
- 에러 응답 형식을 통일한다.
- 페이징, 정렬, 필터링 방식을 정한다.
- 인증이 필요한 API와 공개 API를 구분한다.

<a id="http-error-handling"></a>
## HTTP Error Handling

HTTP 에러 처리는 상태 코드로 요청 결과를 표현하는 것이다.  
PDF에는 `HTTP 3xx, 4xx, 5xx`가 나온다.

### 3xx

3xx는 리다이렉션이다.  
요청한 리소스가 다른 위치에 있거나, 다른 URL로 이동해야 할 때 사용한다.

```text
301 Moved Permanently
302 Found
304 Not Modified
```

### 4xx

4xx는 클라이언트 쪽 요청 문제다.

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
```

### 5xx

5xx는 서버 쪽 문제다.

```text
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
504 Gateway Timeout
```

모든 실패를 500으로 보내면 안 된다.  
사용자가 잘못 입력한 것은 400/422, 인증이 안 된 것은 401, 권한이 없는 것은 403, 서버 내부 장애는 500 계열로 나눠야 한다.

<a id="authentication"></a>
## Authentication

인증은 "너는 누구인가"를 확인하는 과정이다.  
인가 authorization는 "너는 이 작업을 해도 되는가"를 확인하는 과정이다.

```text
인증: 로그인한 사용자인가?
인가: 이 게시글을 수정할 권한이 있는가?
```

Session, JWT, OAuth2, OIDC는 모두 로그인 근처에서 보이지만 같은 역할은 아니다.  
Session과 JWT는 로그인 상태를 우리 서비스가 어떻게 유지할지에 가깝다. OAuth2는 다른 서비스의 권한을 위임받는 방법이고, OIDC는 외부 인증 제공자가 "이 사용자가 누구인지" 알려주는 표준이다.

<a id="session"></a>
## Session

세션은 서버가 로그인 상태를 저장하는 방식이다.

사용자가 로그인하면 서버가 세션을 만들고, 브라우저에는 세션 ID가 담긴 쿠키를 준다.  
이후 요청마다 쿠키를 보내면 서버가 세션 저장소를 확인해서 사용자를 알아낸다.

아래 상황에서 좋다.

- 서버에서 로그인 상태를 직접 관리하고 싶다.
- 로그아웃, 강제 만료, 세션 무효화가 중요하다.
- 브라우저 기반 웹 서비스다.

서버가 세션 저장소를 관리해야 한다.  
서버가 여러 대라면 Redis 같은 공유 세션 저장소가 필요할 수 있다.

<a id="jwt"></a>
## JWT

JWT는 JSON Web Token의 약자다.  
사용자 정보를 담은 토큰을 클라이언트가 보관하고, 요청마다 서버에 보내는 방식이다.

서버는 토큰의 서명을 검증해서 토큰이 위조되지 않았는지 확인한다.

```text
Authorization: Bearer eyJhbGciOi...
```

아래 상황에서 많이 쓴다.

- API 서버와 프론트엔드가 분리되어 있다.
- 모바일 앱, 웹 앱 등 여러 클라이언트가 API를 쓴다.
- 서버가 세션 저장소를 덜 의존하고 싶다.

JWT는 한 번 발급되면 만료 전까지 무효화하기 어렵다.  
그래서 access token은 짧게, refresh token은 안전하게 관리하는 전략이 필요하다.

<a id="oauth2"></a>
## OAuth2

OAuth2는 다른 서비스의 권한을 위임받기 위한 표준 프로토콜이다.  
예를 들어 "Google 계정으로 로그인"이나 "GitHub 저장소 접근 권한 허용" 같은 흐름에 사용된다.

사용자가 직접 비밀번호를 우리 서비스에 주지 않고, 외부 서비스가 발급한 token을 통해 권한을 위임한다.

아래 상황에서 사용한다.

- 소셜 로그인
- 외부 API 접근 권한 위임
- 사용자의 Google Drive, GitHub, Slack 같은 리소스 접근

OAuth2는 인증 자체보다 "권한 위임"에 초점이 있다.  
로그인 목적으로 사용할 때는 OIDC와 함께 이해하는 것이 좋다.

<a id="oidc"></a>
## OIDC

OIDC는 OpenID Connect의 약자다.  
OAuth2 위에 인증 개념을 얹은 표준이다.

OAuth2가 "권한 위임"이라면, OIDC는 "이 사용자가 누구인지" 확인할 수 있게 해준다.  
OIDC에서는 ID Token을 통해 사용자 식별 정보를 받는다.

아래 상황에서 사용한다.

- Google, Kakao, Auth0 같은 외부 인증 제공자를 쓴다.
- 표준 기반 로그인 시스템을 만들고 싶다.
- 기업용 SSO와 연동한다.

OAuth2와 OIDC를 같은 것으로 생각하면 헷갈린다.  
OAuth2는 권한 위임, OIDC는 인증에 더 가깝다.

<a id="realtime"></a>
## Realtime

실시간 기능은 서버의 변화가 사용자 화면에 바로 반영되도록 하는 기능이다.

예를 들어 채팅, 알림, 실시간 로그, 진행 상황 표시, 주식 가격, 게임 상태 같은 기능에서 필요하다.

WebSocket과 SSE는 둘 다 실시간처럼 보이지만 방향성이 다르다.  
서버와 클라이언트가 서로 계속 말해야 하면 WebSocket이 어울리고, 서버가 진행 상황이나 알림을 계속 내려주기만 하면 SSE가 더 단순하다.

<a id="websocket"></a>
## WebSocket

WebSocket은 브라우저와 서버가 양방향으로 계속 연결되어 통신하는 방식이다.

HTTP 요청은 보통 요청과 응답이 끝나면 연결이 종료된다.  
WebSocket은 연결을 유지하면서 클라이언트와 서버가 서로 메시지를 보낼 수 있다.

아래 상황에서 좋다.

- 채팅
- 멀티플레이 게임
- 실시간 협업 편집
- 양방향 알림
- 클라이언트도 서버에 자주 메시지를 보내야 하는 기능

연결 관리, 재연결, 인증, 스케일링을 신경 써야 한다.  
단순히 서버가 진행 상황만 내려주는 경우라면 SSE가 더 간단할 수 있다.

<a id="sse"></a>
## SSE

SSE는 Server-Sent Events이다.  
서버가 브라우저로 이벤트를 계속 보내는 단방향 스트리밍 방식이다.

브라우저가 서버에 연결하면 서버는 이벤트를 계속 흘려보낸다.

```text
client -> server: 연결 시작
server -> client: progress 10%
server -> client: progress 50%
server -> client: done
```

아래 상황에서 좋다.

- 작업 진행 상황 표시
- 서버 로그 스트리밍
- 알림 피드
- AI 응답 스트리밍
- 서버가 주로 보내기만 하는 실시간 기능

### WebSocket과 차이

WebSocket은 양방향, SSE는 서버에서 클라이언트로 보내는 단방향이다.  
단방향이면 SSE가 더 단순하고 HTTP 기반이라 다루기 쉽다.

<a id="security"></a>
## Security

보안은 서비스를 악의적 사용, 실수, 데이터 유출, 권한 오남용으로부터 보호하는 것이다.

백엔드 보안은 단일 기능이 아니라 여러 층의 방어로 이루어진다.

```text
HTTPS
인증/인가
입력 검증
권한 체크
Rate limit
CSRF/CORS
로그와 모니터링
비밀값 관리
```

<a id="https"></a>
## HTTPS

HTTPS는 HTTP 통신을 암호화하는 방식이다.  
TLS를 사용해서 브라우저와 서버 사이의 데이터를 보호한다.

HTTPS는 아래를 제공한다.

- 통신 암호화
- 서버 신원 확인
- 중간자 공격 방지
- 데이터 변조 방지

실서비스에서는 거의 무조건 사용해야 한다.  
로그인, 결제, 개인정보, API token이 오가는 서비스라면 필수다.

<a id="owasp-top-10"></a>
## OWASP Top 10

OWASP Top 10은 웹 애플리케이션에서 자주 발생하는 주요 보안 위험 목록이다.  
보안 입문자가 무엇부터 조심해야 하는지 알려주는 기준표라고 볼 수 있다.

대표적으로 아래 같은 위험을 다룬다.

- Broken Access Control
- Cryptographic Failures
- Injection
- Insecure Design
- Security Misconfiguration
- Vulnerable Components
- Authentication Failures

웹 서비스를 설계하거나 리뷰할 때 체크리스트처럼 사용한다.  
특히 인증, 권한, 입력 검증, 설정, 의존성 보안은 항상 확인해야 한다.

<a id="rate-limit"></a>
## Rate Limit

Rate limit은 사용자가 일정 시간 동안 요청할 수 있는 횟수를 제한하는 것이다.

예를 들어 한 IP가 1분에 로그인 요청을 1000번 보내면 막아야 한다.  
Rate limit은 API 남용, brute force 공격, 비용 폭증을 방지한다.

아래 기능에서 중요하다.

- 로그인
- 회원가입
- 비밀번호 재설정
- 검색 API
- 외부 API나 AI API를 호출하는 엔드포인트

너무 강하게 제한하면 정상 사용자가 불편해질 수 있다.  
사용자 ID, IP, API key 등 어떤 기준으로 제한할지 설계해야 한다.

<a id="csrf-cors"></a>
## CSRF/CORS

CSRF와 CORS는 둘 다 브라우저 보안과 관련 있지만 서로 다른 개념이다.

### CSRF

CSRF는 Cross-Site Request Forgery이다.  
사용자가 로그인한 상태를 악용해서, 공격자가 원하지 않는 요청을 보내게 만드는 공격이다.

쿠키 기반 인증을 사용할 때 특히 주의해야 한다.

### CORS

CORS는 Cross-Origin Resource Sharing이다.  
브라우저가 다른 origin의 API를 호출할 때 허용 여부를 판단하는 정책이다.

```text
frontend.example.com -> api.example.com
```

이렇게 서로 origin이 다르면 서버가 CORS 설정으로 허용해야 한다.

CORS는 보안 기능이지만, 서버 API 자체의 권한 체크를 대신하지 않는다.  
그리고 `*`로 모두 허용하는 설정은 인증 API에서 위험할 수 있다.

<a id="asynchronous-processing"></a>
## Asynchronous Processing

비동기 처리는 요청을 받은 즉시 모든 일을 끝내지 않고, 시간이 오래 걸리는 작업을 뒤로 넘기는 방식이다.

예를 들어 이메일 발송, 이미지 변환, 대용량 파일 처리, 외부 API 호출, 리포트 생성은 오래 걸릴 수 있다.  
이런 작업을 요청-응답 흐름 안에서 모두 처리하면 사용자가 오래 기다려야 한다.

```text
요청 받음
-> 작업을 큐에 넣음
-> 바로 응답
-> 백그라운드 worker가 처리
```

<a id="job-queue"></a>
## Job Queue

Job Queue는 나중에 처리할 작업을 줄 세워두는 구조다.

서버는 작업을 queue에 넣고, worker는 queue에서 작업을 꺼내 처리한다.

```text
API 서버 -> Queue -> Worker
```

비동기 처리를 이해할 때 `async`와 `job queue`를 섞어 생각하면 헷갈린다.  
`async`는 한 서버 프로세스 안에서 기다리는 시간을 효율적으로 쓰는 방식이고, `job queue`는 오래 걸리는 일을 아예 다른 worker에게 넘기는 구조다.

아래 상황에서 사용한다.

- 이메일 발송
- 이미지/영상 처리
- 리포트 생성
- 외부 API 재시도
- 시간이 오래 걸리는 AI 처리

작업 실패, 재시도, 중복 실행, 순서 보장, 작업 상태 저장을 고려해야 한다.

<a id="rabbitmq"></a>
## RabbitMQ

RabbitMQ는 메시지 브로커다.  
작업이나 메시지를 queue에 넣고 consumer가 가져가 처리하는 구조를 제공한다.

아래 상황에서 좋다.

- 명확한 작업 큐가 필요하다.
- producer와 consumer를 분리하고 싶다.
- 메시지 라우팅, 재시도, ack 처리가 필요하다.

### Kafka와 차이

RabbitMQ는 작업 큐와 메시지 라우팅에 강하고, Kafka는 대규모 이벤트 스트림과 로그 처리에 강하다.

<a id="kafka"></a>
## Kafka

Kafka는 대규모 이벤트 스트리밍 플랫폼이다.  
메시지를 topic에 저장하고 여러 consumer가 읽어갈 수 있다.

아래 상황에서 많이 쓴다.

- 대용량 이벤트 처리
- 로그 수집
- 실시간 데이터 파이프라인
- 여러 서비스가 같은 이벤트를 구독해야 하는 구조

Kafka는 강력하지만 운영 난이도가 있다.  
단순한 백그라운드 작업 큐에는 RabbitMQ나 Redis Queue가 더 단순할 수 있다.

<a id="asynchronous-programming"></a>
## Asynchronous Programming

비동기 프로그래밍은 프로그램이 어떤 작업이 끝날 때까지 마냥 기다리지 않고 다른 작업을 처리할 수 있게 하는 방식이다.

예를 들어 외부 API 호출, DB 조회, 파일 읽기처럼 기다리는 시간이 있는 작업에서 중요하다.

<a id="async"></a>
## Async

Async는 비동기 함수를 표현하는 키워드나 개념이다.

Python에서는 `async def`, JavaScript에서는 `async function`을 사용한다.

```py
async def fetch_data():
    result = await call_api()
    return result
```

```ts
async function fetchData() {
  const result = await callApi();
  return result;
}
```

아래 상황에서 사용한다.

- HTTP API 호출
- DB I/O
- 파일 I/O
- WebSocket/SSE
- 여러 I/O 작업을 효율적으로 처리해야 할 때

비동기는 CPU 작업을 자동으로 빠르게 해주는 것이 아니다.  
주로 I/O 대기 시간을 효율적으로 다루는 방식이다.

<a id="event-loop"></a>
## Event Loop

이벤트 루프는 비동기 작업을 관리하는 실행 구조다.

이벤트 루프는 지금 실행할 수 있는 작업을 처리하고, 기다려야 하는 작업은 나중에 다시 이어서 처리한다.

```text
작업 시작
-> I/O 대기
-> 다른 작업 처리
-> I/O 완료
-> 원래 작업 이어서 처리
```

JavaScript/Node.js, Python asyncio 기반 서버에서 중요하다.  
비동기 서버를 만들 때 이벤트 루프를 이해하지 못하면 blocking 코드 때문에 성능 문제가 생길 수 있다.

<a id="caching"></a>
## Caching

캐싱은 자주 쓰는 데이터를 더 빠른 곳에 임시로 저장하는 것이다.

매번 DB나 외부 API를 호출하지 않고, 이전 결과를 저장해두었다가 재사용한다.

```text
요청
-> 캐시에 있음: 바로 반환
-> 캐시에 없음: DB 조회 후 캐시에 저장
```

아래 상황에서 좋다.

- 자주 조회되지만 자주 바뀌지 않는 데이터
- 외부 API 호출 비용이 큰 데이터
- 로그인 세션
- rate limit 카운터
- 랭킹, 인기글, 설정값

캐시는 오래된 데이터를 줄 수 있다.  
언제 만료할지, 언제 갱신할지, 삭제할지 정해야 한다.

<a id="redis"></a>
## Redis

Redis는 메모리 기반의 빠른 key-value 저장소다.  
DB보다 훨씬 빠르게 읽고 쓸 수 있어서 캐시, 세션, 큐, rate limit 등에 많이 사용된다.

아래 상황에서 많이 쓴다.

- 캐싱
- 세션 저장
- rate limit 카운터
- 간단한 queue
- 분산 락
- 실시간 랭킹

Redis는 기본적으로 메모리 기반이라 저장 공간과 persistence 설정을 신경 써야 한다.  
영구 데이터의 메인 DB로 쓰기보다는 보조 저장소로 쓰는 경우가 많다.

<a id="logging"></a>
## Logging

로깅은 시스템에서 일어난 일을 기록하는 것이다.

로그는 장애 분석, 사용자 행동 추적, 보안 감사, 성능 분석에 사용된다.

```text
INFO: user logged in
WARN: rate limit exceeded
ERROR: database connection failed
```

서비스가 배포되고 나면 디버거로 직접 볼 수 없다.  
문제가 생겼을 때 로그가 없으면 원인을 찾기 어렵다.

비밀번호, token, 개인정보를 로그에 남기면 안 된다.  
로그 레벨과 포맷을 일관되게 관리해야 한다.

<a id="backend-testing"></a>
## Testing

백엔드 테스트는 API와 비즈니스 로직이 의도대로 동작하는지 검증한다.

- 입력 검증
- 인증/권한
- 비즈니스 규칙
- DB 저장/조회
- API 응답 형식
- 에러 처리

백엔드는 데이터와 권한을 다루기 때문에 프론트엔드보다 실패 비용이 클 수 있다.  
특히 로그인, 결제, 권한 체크, 데이터 수정 API는 테스트가 중요하다.

<a id="configuration"></a>
## Configuration

설정은 코드가 실행되는 환경에 따라 달라지는 값을 관리하는 것이다.

아래 값들은 코드에 직접 박아두지 않고 설정으로 관리한다.

- DB URL
- API key
- secret key
- 외부 서비스 endpoint
- 로그 레벨
- 배포 환경

로컬, 개발, 스테이징, 운영 환경은 설정이 다르다.  
설정을 잘 분리해야 같은 코드로 여러 환경에서 안전하게 실행할 수 있다.

secret key나 API key를 Git에 올리면 안 된다.  
`.env`, secret manager, 환경 변수 등을 사용한다.
