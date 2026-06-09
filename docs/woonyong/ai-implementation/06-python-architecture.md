# 06. Python Architecture

AI 백엔드는 Python으로 구현하되, 단순 스크립트처럼 만들면 금방 복잡해진다.  
추천 구조는 `Modular Monolith + Layered Architecture + Ports and Adapters`다.

```text
Modular Monolith
- 하나의 FastAPI 앱으로 시작
- 내부 모듈 경계를 명확히 나눔

Layered Architecture
- API, application, domain, infrastructure를 분리

Ports and Adapters
- LLM, Vector DB, MCP, DB 접근을 interface로 감싸 교체 가능하게 만듦
```

## Recommended Package Structure

```text
apps/api/src/app
├── main.py
├── core
│   ├── config.py
│   ├── logging.py
│   ├── security.py
│   └── errors.py
├── modules
│   ├── auth
│   ├── board
│   └── ai
│       ├── presentation
│       │   ├── ai_router.py
│       │   ├── sse_router.py
│       │   └── schemas.py
│       ├── application
│       │   ├── run_agent_use_case.py
│       │   ├── ingest_document_use_case.py
│       │   ├── retrieve_context_use_case.py
│       │   └── generate_answer_use_case.py
│       ├── domain
│       │   ├── models.py
│       │   ├── value_objects.py
│       │   ├── ports.py
│       │   ├── policies.py
│       │   └── events.py
│       └── infrastructure
│           ├── openai_llm_client.py
│           ├── openai_embedding_client.py
│           ├── pgvector_store.py
│           ├── mcp_tool_client.py
│           ├── langgraph_agent_runner.py
│           └── repositories.py
└── db
    ├── session.py
    └── migrations
```

이 구조에서 각 계층의 역할은 분명하다.

```text
presentation
- FastAPI router
- request/response schema
- SSE event 변환

application
- use case
- transaction 흐름
- domain 객체와 port 조합

domain
- 핵심 모델
- 정책
- interface
- 외부 기술을 모르는 순수 규칙

infrastructure
- OpenAI API
- pgvector
- SQLAlchemy
- MCP client
- LangGraph 구현체
```

## OOP Boundary

Python에서 객체지향은 "클래스를 많이 만드는 것"이 아니다.  
상태와 책임이 있는 곳, 교체 가능성이 필요한 곳, 테스트에서 fake로 대체해야 하는 곳을 class/interface로 잡는다.

클래스로 두기 좋은 것:

```text
LLMClient
EmbeddingClient
VectorStore
Retriever
MCPToolClient
AgentRunner
AgentPolicy
AgentRunRepository
MemoryRepository
UnitOfWork
```

함수로 두기 좋은 것:

```text
normalize_text()
split_chunks()
estimate_tokens()
format_citation()
merge_search_results()
sanitize_tool_output()
```

기준은 간단하다.

```text
상태가 있다        -> class 후보
외부 의존성이 있다  -> class/port 후보
테스트 대체가 필요  -> Protocol 후보
순수 변환이다       -> function 후보
```

## Domain Model

Domain model은 DB 모델과 같지 않다.  
DB 모델은 저장을 위한 구조이고, domain model은 서비스 규칙을 표현하는 구조다.

```python
from pydantic import BaseModel


class AgentRun(BaseModel):
    id: str
    user_id: str
    status: str
    step_count: int = 0

    def can_continue(self, max_steps: int) -> bool:
        return self.status == "running" and self.step_count < max_steps

    def mark_failed(self, reason: str) -> None:
        self.status = "failed"
```

domain model은 FastAPI, SQLAlchemy, OpenAI SDK를 몰라야 한다.  
그래야 테스트하기 쉽고, 외부 기술이 바뀌어도 핵심 규칙이 덜 흔들린다.

## Use Case

Use case는 하나의 사용자 행동 또는 시스템 작업을 처리한다.

```python
class RunAgentUseCase:
    def __init__(
        self,
        agent_runner: AgentRunner,
        run_repository: AgentRunRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.agent_runner = agent_runner
        self.run_repository = run_repository
        self.unit_of_work = unit_of_work

    async def execute(self, command: RunAgentCommand) -> AgentRunResult:
        async with self.unit_of_work:
            run = await self.run_repository.create(command.to_run())

        result = await self.agent_runner.run(run.id, command.user_input)

        async with self.unit_of_work:
            await self.run_repository.save_result(run.id, result)

        return result
```

use case는 HTTP request를 몰라도 되고, OpenAI SDK의 세부 객체도 몰라도 된다.  
그 대신 "이 작업을 처리하기 위해 어떤 port를 어떤 순서로 호출할지"를 안다.

## Repository

Repository는 DB 접근을 감싼다.

```python
from typing import Protocol


class AgentRunRepository(Protocol):
    async def create(self, run: AgentRun) -> AgentRun:
        ...

    async def get(self, run_id: str) -> AgentRun | None:
        ...

    async def save_result(self, run_id: str, result: AgentRunResult) -> None:
        ...
```

SQLAlchemy 구현체는 infrastructure에 둔다.

```python
class SQLAlchemyAgentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, run_id: str) -> AgentRun | None:
        row = await self.session.get(AgentRunORM, run_id)
        return to_domain(row) if row else None
```

Repository를 쓰면 application layer가 SQLAlchemy 쿼리를 직접 알 필요가 없다.

## Unit of Work

Unit of Work는 transaction 경계를 관리한다.

```python
class UnitOfWork(Protocol):
    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(self, exc_type, exc, tb) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...
```

AI 기능에서도 transaction은 중요하다.

```text
agent_run 생성
agent_step 저장
tool_call 로그 저장
usage 로그 저장
memory write
```

이 작업들이 중간에 실패하면 상태가 어긋날 수 있다.  
따라서 DB 변경 작업은 명확한 transaction 경계 안에서 처리한다.

## Dependency Injection

FastAPI의 dependency를 사용해서 use case를 조립한다.

```python
async def get_run_agent_use_case(
    session: AsyncSession = Depends(get_session),
) -> RunAgentUseCase:
    uow = SQLAlchemyUnitOfWork(session)
    run_repo = SQLAlchemyAgentRunRepository(session)
    llm_client = OpenAILLMClient(settings.openai_api_key)
    retriever = PgVectorRetriever(session, llm_client)
    mcp_client = MCPToolClient(...)
    agent_runner = LangGraphAgentRunner(llm_client, retriever, mcp_client)

    return RunAgentUseCase(agent_runner, run_repo, uow)
```

처음에는 이렇게 직접 조립해도 된다.  
나중에 의존성이 많아지면 container를 따로 둘 수 있지만, 초반부터 복잡한 DI 프레임워크를 넣을 필요는 없다.

## Error Model

에러는 계층별로 나누는 것이 좋다.

```text
DomainError
- 정책 위반
- 상태 전이 불가

ApplicationError
- use case 처리 실패
- 권한 없음

InfrastructureError
- OpenAI API 실패
- DB 실패
- MCP tool 실패

Presentation Error
- HTTP status code로 변환
```

예시:

```python
class AppError(Exception):
    code: str = "app_error"


class ToolPermissionDenied(AppError):
    code = "tool_permission_denied"


class AgentStepLimitExceeded(AppError):
    code = "agent_step_limit_exceeded"
```

FastAPI router에서는 이 에러를 HTTP 응답이나 SSE `agent.failed` 이벤트로 바꾼다.

## Test Strategy

AI 백엔드 테스트는 일반 백엔드 테스트와 조금 다르다.

```text
Unit Test
- chunk splitter
- context builder
- policy
- tool argument validator

Integration Test
- pgvector search
- repository
- MCP client/server
- FastAPI endpoint

Agent Scenario Test
- 특정 질문에 대해 기대 action sequence가 나오는지

Evaluation Test
- golden dataset으로 RAG/Agent 품질 비교
```

LLM 호출은 테스트에서 fake client로 대체한다.

```python
class FakeLLMClient:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = outputs

    async def generate_structured(self, *args, **kwargs):
        return self.outputs.pop(0)
```

이렇게 해야 테스트가 빠르고 비용이 들지 않는다.  
실제 OpenAI API를 호출하는 테스트는 별도의 integration/evaluation 단계에서 제한적으로 실행한다.

## 구현 순서

```text
1. domain port 정의
2. fake 구현체로 use case 테스트 작성
3. infrastructure 구현체 연결
4. FastAPI router 연결
5. 실제 LLM/RAG/MCP integration 테스트
6. evaluation dataset 추가
```

이 순서로 가면 처음부터 외부 API와 DB에 끌려다니지 않고, 핵심 흐름을 먼저 설계할 수 있다.

