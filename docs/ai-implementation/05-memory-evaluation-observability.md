# 05. Memory, Evaluation, Observability

참고:

- [OpenAI Conversation State](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses)
- [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangGraph Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- [OpenAI Agents SDK Tracing](https://openai.github.io/openai-agents-python/tracing/)

AI 기능은 "답변이 한 번 잘 나오는 것"보다 "왜 그렇게 답했는지, 다시 실행해도 좋아지는지, 실패했을 때 어디가 문제인지"가 더 중요하다.  
Memory, Evaluation, Observability는 그걸 가능하게 하는 운영 품질 계층이다.

## Memory

Memory는 모델이 사용자의 맥락을 계속 활용할 수 있게 저장하고 꺼내는 구조다.  
RAG와 비슷해 보이지만 목적이 다르다.

```text
RAG
- 외부 지식 검색
- 게시글, 문서, FAQ, GitHub issue 같은 지식 기반

Memory
- 사용자와 작업 맥락 기억
- 선호, 이전 대화 요약, 프로젝트 상태, 반복 규칙
```

RAG는 "자료를 찾는 것"이고, Memory는 "사용자와 서비스의 맥락을 기억하는 것"에 가깝다.

## Short-term Memory

Short-term memory는 현재 대화나 현재 agent run 안에서만 필요한 기억이다.

```text
현재 사용자 메시지
최근 대화 몇 턴
이번 run에서 검색한 RAG 결과
이번 run에서 호출한 tool 결과
현재 작성 중인 답변 초안
승인 대기 중인 action
```

Short-term memory는 보통 agent state에 들어간다.

```python
class AgentState(BaseModel):
    messages: list[dict]
    observations: list[dict]
    selected_sources: list[str]
    pending_actions: list[dict]
    final_answer: str | None = None
```

이 memory는 run이 끝나면 그대로 저장하되, 다음 대화에 전부 넣지는 않는다.  
다음 대화에는 최근 메시지 일부와 요약만 넣는 편이 token budget에 안전하다.

## Long-term Memory

Long-term memory는 여러 대화와 세션을 넘어 유지되는 기억이다.

```text
사용자가 선호하는 답변 스타일
사용자가 진행 중인 프로젝트
자주 쓰는 기술 스택
이전에 합의한 규칙
반복되는 문제 해결 패턴
```

예를 들어 아래는 long-term memory가 될 수 있다.

```json
{
  "namespace": "user_preferences",
  "key": "answer_style",
  "value": {
    "language": "ko",
    "prefers_keyword_tree_docs": true,
    "prefers_detailed_implementation_notes": true
  }
}
```

하지만 아무 내용이나 long-term memory로 저장하면 안 된다.  
잘못 저장된 memory는 이후 답변을 계속 오염시킨다.

## Memory Write Policy

Long-term memory는 명확한 기준이 있을 때만 저장한다.

```text
저장하면 좋은 것
- 사용자가 명시적으로 선호를 말함
- 여러 번 반복된 작업 패턴
- 프로젝트에서 합의한 기술 선택
- 장기적으로 참조할 팀 규칙

저장하면 안 되는 것
- 일회성 감정 표현
- 불확실한 추측
- 민감 정보
- API key, token, 비밀번호
- 사용자가 임시로 말한 내용
```

Memory write는 Agent가 마음대로 하지 않게 하는 것이 좋다.  
처음에는 application code가 명시적으로 저장하고, 나중에 Agent가 memory 후보를 제안하면 사람이 승인하는 방식으로 확장한다.

## Memory Retrieval

Memory도 RAG처럼 검색이 필요하다.  
하지만 모든 memory를 매번 prompt에 넣으면 안 된다.

```text
1. 현재 요청과 관련 있는 memory 후보 검색
2. 너무 오래되었거나 신뢰 낮은 memory 제외
3. 현재 작업에 필요한 memory만 prompt에 삽입
4. 사용한 memory id를 agent run에 기록
```

Memory에는 confidence와 updated_at을 두면 좋다.

```json
{
  "id": "mem_123",
  "namespace": "project_preferences",
  "content": "Python backend는 FastAPI로 고정한다.",
  "confidence": 0.95,
  "updated_at": "2026-06-06T12:00:00+09:00"
}
```

## Evaluation

AI 기능은 테스트하기 어렵다.  
같은 질문에도 답변이 조금씩 달라질 수 있고, 정답이 하나가 아닌 경우도 많다. 그래서 일반 unit test와 다른 평가 방식이 필요하다.

평가는 세 층으로 나눈다.

```text
Retrieval Evaluation
- RAG가 맞는 자료를 찾았는가

Generation Evaluation
- LLM 답변이 정확하고 근거에 맞는가

Agent Evaluation
- Agent가 올바른 순서로 tool을 쓰고 멈췄는가
```

## RAG Evaluation

RAG 평가는 답변보다 검색을 먼저 본다.

```text
질문: "JWT 인증 실패 관련 글 찾아줘"
기대 source: post_123, comment_991

검사
- post_123이 top-5 안에 있는가
- comment_991이 top-10 안에 있는가
- 엉뚱한 OAuth 일반 설명 문서만 나오지 않는가
```

지표:

```text
Recall@k
- 정답 source가 top-k 안에 있는 비율

MRR
- 정답 source가 얼마나 높은 순위에 있는지

Precision@k
- top-k 중 실제 관련 있는 문서 비율

Filter Accuracy
- tag/date/user filter가 제대로 적용됐는지
```

## Generation Evaluation

답변 평가는 "그럴듯함"이 아니라 근거와 사용성을 본다.

```text
Groundedness
- 답변이 제공된 context 안에 근거를 가지고 있는가

Citation Accuracy
- citation이 실제 답변 내용을 뒷받침하는가

Completeness
- 질문의 핵심 요구를 빠뜨리지 않았는가

Abstention
- 근거가 부족할 때 모른다고 말하는가

Tone / Format
- 서비스가 요구한 말투와 형식을 지키는가
```

LLM이 평가자가 될 수도 있지만, 모든 평가를 LLM에게 맡기면 평가 자체도 흔들릴 수 있다.  
처음에는 사람이 만든 golden dataset과 규칙 기반 검사를 섞는 것이 좋다.

## Agent Evaluation

Agent 평가는 실행 경로를 본다.

```text
질문: "이 에러와 비슷한 GitHub 이슈도 찾아줘"

기대 행동
1. intent 분류
2. RAG 검색
3. MCP GitHub issue 검색
4. 결과 통합
5. citation 포함 답변

실패 행동
- RAG 없이 일반 답변
- 같은 MCP tool 5회 반복
- GitHub issue 생성 같은 write tool을 승인 없이 실행
```

Agent 평가는 step trace가 있어야 가능하다.  
그래서 agent_steps 저장과 observability가 중요하다.

## Golden Dataset

Golden dataset은 평가용 질문과 기대 결과 모음이다.

```json
{
  "id": "eval_rag_001",
  "question": "FastAPI JWT 인증 실패 원인을 찾아줘",
  "expected_sources": ["post_123", "comment_991"],
  "expected_actions": ["classify_intent", "rag_search", "generate_answer"],
  "must_include": ["Authorization 헤더", "Bearer", "토큰 만료"],
  "must_not_include": ["근거 없이 OAuth2 설정 문제라고 단정"]
}
```

변경 전후로 같은 golden dataset을 돌려야 개선 여부를 알 수 있다.

```text
chunking 변경 전/후
embedding model 변경 전/후
retriever query rewrite 추가 전/후
reranker 추가 전/후
prompt 변경 전/후
```

## Observability

Observability는 AI 기능을 들여다볼 수 있게 만드는 것이다.

일반 API에서는 status code와 latency만 봐도 어느 정도 알 수 있다.  
하지만 Agent는 내부에서 LLM 호출, RAG 검색, tool 호출, 재시도, 검증이 일어난다. 그래서 더 자세한 trace가 필요하다.

## Trace

Trace는 하나의 agent run 전체 실행 기록이다.

```text
trace
├── classify_intent
├── rewrite_query
├── retrieve_context
├── call_mcp_tool
├── generate_answer
└── verify_answer
```

각 span에는 아래 정보를 남긴다.

```text
span_name
input_summary
output_summary
latency_ms
status
error_code
token_usage
tool_name
source_ids
```

OpenAI Agents SDK의 tracing 문서도 agent run, LLM generation, function tool calls, guardrails, handoffs 등을 trace로 수집한다고 설명한다.  
직접 구현하더라도 같은 관점으로 로그를 남기면 디버깅이 쉬워진다.

## Metrics

운영 지표는 기술별로 나눠 본다.

```text
LLM
- request count
- latency
- input/output tokens
- cost
- structured output failure rate

RAG
- retrieval latency
- top-k hit rate
- no-result rate
- average context tokens

MCP
- tool call count
- tool latency
- tool failure rate
- approval required count

Agent
- run success rate
- average steps
- max step exceeded count
- timeout count
- human approval wait count
```

이 지표가 있어야 "느리다", "비싸다", "자주 틀린다"를 구체적으로 볼 수 있다.

## Cost Tracking

AI 서비스는 비용 추적이 필수다.

```sql
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY,
    agent_run_id UUID,
    user_id UUID NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_type TEXT NOT NULL,
    input_tokens INT NOT NULL,
    output_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    estimated_cost NUMERIC(12, 6),
    latency_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

비용을 줄이는 방법:

```text
간단한 분류는 작은 모델 사용
RAG context 중복 제거
tool output 요약 후 삽입
대화 기록 요약
embedding content_hash 캐시
동일 질문에 대한 짧은 TTL 캐시
```

## Debug Dashboard

AI 기능에는 개발자용 디버그 화면이 있으면 좋다.

```text
Agent Run Detail
- user input
- final answer
- status
- total latency
- total token usage

Step Timeline
- intent classification
- RAG search
- MCP tool call
- answer generation

RAG Debug
- rewritten query
- retrieved chunks
- scores
- source links

Tool Debug
- tool name
- arguments
- result summary
- error

Prompt Debug
- 실제 prompt preview
- context token count
- system/developer instruction version
```

디버그 화면이 없으면 RAG가 틀렸는지, tool이 틀렸는지, prompt가 틀렸는지 감으로만 봐야 한다.

