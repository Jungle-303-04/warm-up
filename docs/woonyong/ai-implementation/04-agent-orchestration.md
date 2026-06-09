# 04. Agent Orchestration

참고:

- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph)
- [LangGraph Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- [LangGraph Agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)
- [OpenAI Agents SDK Handoffs](https://openai.github.io/openai-agents-python/handoffs/)

Agent는 LLM을 이용해 여러 단계를 실행하는 orchestration 구조다.  
여기서 중요한 것은 "AI가 알아서 다 한다"가 아니라, 우리가 정한 안전한 실행 루프 안에서 LLM에게 판단 일부를 맡긴다는 점이다.

## Workflow와 Agent의 차이

Workflow는 흐름이 고정되어 있다.

```text
질문
-> RAG 검색
-> 답변 생성
```

Agent는 중간 판단이 들어간다.

```text
질문
-> LLM이 "검색 필요" 판단
-> RAG 검색
-> 결과 부족 판단
-> query rewrite
-> 재검색
-> 답변 생성
```

처음에는 workflow로 시작하고, 분기와 반복이 필요해지는 지점에 Agent를 도입하는 것이 좋다.

## Agent State

Agent는 상태를 가져야 한다.  
상태 없이 매 단계 LLM만 호출하면 이전 단계에서 무엇을 했는지 추적할 수 없다.

```python
from typing import Literal
from pydantic import BaseModel


class AgentObservation(BaseModel):
    type: str
    content: str
    metadata: dict = {}


class AgentState(BaseModel):
    run_id: str
    user_id: str
    user_input: str
    intent: str | None = None
    step_count: int = 0
    status: Literal["running", "waiting_approval", "completed", "failed"] = "running"
    observations: list[AgentObservation] = []
    rag_context_ids: list[str] = []
    pending_tool_calls: list[dict] = []
    final_answer: str | None = None
```

상태에는 최소한 아래가 들어가야 한다.

```text
사용자 요청
현재 단계
의도 분류 결과
검색 결과
tool 호출 결과
에러
최종 답변
승인 대기 action
```

## 직접 구현하는 Agent Loop

학습 목적이라면 처음에는 직접 loop를 구현하는 것이 좋다.

```python
async def run_agent(state: AgentState) -> AgentState:
    for _ in range(MAX_STEPS):
        action = await planner.decide_next_action(state)

        if action.type == "final_answer":
            state.final_answer = action.answer
            state.status = "completed"
            return state

        if action.type == "rag_search":
            chunks = await retriever.retrieve(action.query, action.filters, action.limit)
            state.observations.append(to_observation(chunks))
            continue

        if action.type == "mcp_tool_call":
            result = await mcp_client.call_tool(action.tool_call)
            state.observations.append(to_observation(result))
            continue

        if action.type == "approval_required":
            state.pending_tool_calls.append(action.tool_call)
            state.status = "waiting_approval"
            return state

    state.status = "failed"
    state.observations.append(AgentObservation(type="error", content="max steps exceeded"))
    return state
```

이 구조에서 LLM은 `decide_next_action` 안에서 사용된다.  
실행 자체는 서버가 한다.

## Action 종류

Agent가 선택할 수 있는 action은 제한해야 한다.

```text
answer_directly
- RAG/tool 없이 답변

rewrite_query
- 검색어를 다시 작성

rag_search
- 게시글/문서 검색

mcp_tool_call
- 외부 도구 호출

ask_clarification
- 사용자에게 추가 질문

request_approval
- write tool 실행 전 승인 요청

final_answer
- 최종 답변 반환
```

action schema를 고정하면 루프가 안정된다.  
모델이 임의 문자열로 행동을 설명하게 두면 서버가 실행하기 어렵다.

## Stop Conditions

Agent는 반드시 멈출 조건이 있어야 한다.

```text
max_steps
- 예: 6단계 이상 반복 금지

max_tool_calls
- 예: 한 run에서 tool 5회 초과 금지

timeout
- 예: 전체 60초 초과 시 중단

same_action_repeat
- 같은 query로 같은 tool 반복 호출 금지

confidence_threshold
- 확신이 낮으면 사용자에게 질문

approval_boundary
- 변경 작업은 승인 전 중단
```

무한 루프 방지는 기능이 아니라 필수 안전장치다.

## LangGraph를 쓰는 이유

직접 loop는 학습에 좋지만, 운영 수준으로 가면 복잡해진다.

```text
중간 상태 저장
실패 후 재개
human-in-the-loop
streaming
분기 그래프
노드별 retry
디버깅 trace
```

LangGraph는 이런 long-running, stateful workflow를 다루는 데 강하다.  
공식 문서에서도 durable execution, streaming, human-in-the-loop, memory를 핵심 장점으로 설명한다.

## LangGraph 노드 예시

```text
START
-> classify_intent
-> route_intent
   -> direct_answer
   -> rewrite_query
      -> retrieve_context
      -> grade_context
         -> rewrite_query  (부족하면 반복)
         -> generate_answer
   -> plan_tool_call
      -> call_mcp_tool
      -> generate_answer
-> verify_answer
-> END
```

Agentic RAG는 아래처럼 검색 품질을 스스로 판단하는 구조가 된다.

```text
retrieve_context
-> grade_context
-> if insufficient: rewrite_query
-> if sufficient: generate_answer
```

## Multi-Agent를 언제 나누나

처음부터 여러 Agent를 만들면 복잡도만 늘 수 있다.  
역할이 분명해졌을 때만 나눈다.

```text
나눌 가치가 있는 경우
- 서로 다른 도구를 사용한다.
- 서로 다른 prompt와 정책이 필요하다.
- 서로 다른 출력 형식이 필요하다.
- 한 Agent의 context가 너무 커진다.

나누지 않는 편이 나은 경우
- 이름만 다르고 실제 하는 일이 같다.
- 모든 Agent가 같은 tool과 같은 prompt를 쓴다.
- handoff 이유를 설명할 수 없다.
```

## Manager Pattern

하나의 Orchestrator가 전문 tool/agent를 호출한다.

```text
Orchestrator
-> RetrieverAgent as tool
-> GitHubToolAgent as tool
-> WriterAgent as tool
```

장점은 전체 흐름을 한 곳에서 볼 수 있다는 것이다.  
단점은 Orchestrator prompt가 커지고, 판단 부담이 커질 수 있다는 점이다.

## Handoff Pattern

한 Agent가 다른 Agent에게 대화를 넘긴다.  
OpenAI Agents SDK 문서에서도 handoff는 전문 agent가 대화를 이어받는 방식으로 설명된다.

```text
GeneralAgent
-> "이건 GitHub 분석이 필요하다"
-> GitHubAgent로 handoff
```

handoff는 전문성이 뚜렷할 때 좋다.  
하지만 handoff 후에도 전체 run trace와 사용 권한은 유지되어야 한다.

## Agent Policy

AgentPolicy는 Agent가 해도 되는 일과 안 되는 일을 정한다.

```python
from pydantic import BaseModel


class AgentPolicy(BaseModel):
    max_steps: int = 6
    max_tool_calls: int = 5
    timeout_seconds: int = 60
    allow_write_tools: bool = False
    require_approval_for_tools: list[str] = []
```

policy는 prompt가 아니라 서버 코드로 강제해야 한다.  
프롬프트에 "하지 마"라고 적는 것만으로는 안전장치가 아니다.

## Agent Run 저장

```sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status TEXT NOT NULL,
    input TEXT NOT NULL,
    final_answer TEXT,
    step_count INT NOT NULL DEFAULT 0,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_steps (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES agent_runs(id),
    step_index INT NOT NULL,
    action_type TEXT NOT NULL,
    action_input JSONB NOT NULL,
    observation JSONB,
    status TEXT NOT NULL,
    latency_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

이 테이블이 있어야 나중에 "왜 이런 답변이 나왔는지" 추적할 수 있다.

## SSE 이벤트

Agent run은 프론트에 이벤트를 계속 보낸다.

```json
{
  "type": "rag.search_completed",
  "run_id": "run_123",
  "message": "관련 게시글 4개를 찾았습니다.",
  "payload": {
    "count": 4
  }
}
```

이벤트 종류:

```text
agent.started
intent.classified
rag.search_started
rag.search_completed
mcp.tool_started
mcp.tool_completed
approval.required
answer.delta
answer.completed
agent.failed
```

## Agent 실패 패턴

```text
같은 tool 반복
- same_action_repeat 감지

검색 결과 부족
- clarification 또는 "근거 부족" 답변

tool 실패
- fallback 답변 또는 재시도

JSON parsing 실패
- structured output 사용, schema 재시도

사용자 요청이 너무 넓음
- scope를 좁히는 질문

긴 실행 시간
- SSE로 진행 상황 전달, timeout 후 resume 가능하게 저장
```

