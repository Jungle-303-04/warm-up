# 01. LLM Runtime

참고:

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create?api-mode=responses)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling?api-mode=responses)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat)
- [OpenAI Conversation State](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

LLM Runtime은 모델 API를 호출하는 부분만 뜻하지 않는다.  
서비스 안에서 LLM을 안정적으로 쓰기 위해 필요한 호출 방식, 프롬프트 구성, 구조화 출력, 도구 호출, 스트리밍, 비용/토큰 관리, 실패 처리를 묶은 실행 계층이다.

## LLM을 하나의 함수처럼 보면 안 되는 이유

처음에는 아래처럼 생각하기 쉽다.

```text
question -> LLM -> answer
```

하지만 실제 서비스에서는 요청마다 필요한 일이 다르다.

```text
사용자 질문
-> 이것이 검색이 필요한 질문인가?
-> 검색이 필요하면 어떤 검색어로 바꿀까?
-> 외부 도구가 필요하면 어떤 tool을 어떤 인자로 호출할까?
-> 답변은 JSON이어야 하나, Markdown이어야 하나?
-> 근거가 부족하면 모른다고 해야 하나?
-> 사용자가 기다리는 동안 어떤 진행 상태를 보여줄까?
```

그래서 LLM Runtime은 여러 종류의 호출을 제공해야 한다.

```text
generate_text()
- 일반 답변, 요약, 글 초안 생성

generate_structured()
- JSON schema에 맞춘 분류, 계획, 점수, 태그 생성

stream_text()
- 답변을 token/event 단위로 프론트에 전달

decide_tool_call()
- Function Calling으로 tool 이름과 인자 생성

embed_texts()
- RAG 검색용 embedding 생성

moderate_or_guard()
- 입력/출력 위험성, 정책 위반, prompt injection 징후 점검
```

## Responses API를 중심으로 보는 이유

Responses API는 텍스트 생성뿐 아니라 stateful interaction, tool 사용, streaming, structured output 같은 agentic workflow에 필요한 기능을 한쪽으로 모아 다룰 수 있다.  
문서 기준으로 Responses API는 function calling을 통해 모델이 우리 코드나 외부 시스템에 접근하도록 만들 수 있고, streaming event로 진행 상태를 받을 수 있다.

우리 서비스에서는 OpenAI API 자체의 대화 상태 기능을 무조건 전부 맡기기보다, DB에 자체 대화/실행 상태를 저장하는 쪽이 낫다. 이유는 단순하다.

```text
우리 DB에 저장해야 하는 것
- 사용자 ID
- 게시판 글/댓글과 연결된 AI run
- RAG 검색 결과
- MCP tool 호출 로그
- 비용/토큰 사용량
- 실패/재시도 이력
- 사용자에게 보여준 진행 이벤트
```

OpenAI의 `previous_response_id`나 Conversations API는 대화 상태 관리에 도움이 될 수 있지만, 서비스 전체의 감사 로그와 도메인 상태까지 대신해주지는 않는다.  
따라서 기본 전략은 "서비스 상태는 우리 DB가 소유하고, 모델 호출에는 필요한 context만 넘긴다"가 좋다.

## Prompt 구성

프롬프트는 하나의 긴 문자열이 아니라 여러 층으로 나누는 것이 좋다.

```text
System / Developer Instruction
- 서비스의 역할
- 절대 지켜야 할 정책
- 답변 형식
- tool 사용 규칙

Task Instruction
- 이번 요청에서 해야 할 일
- 예: 게시글 요약, 중복 글 검색, GitHub 이슈 확인

Context
- RAG 검색 결과
- MCP tool 결과
- 현재 사용자/게시글/대화 상태

User Input
- 사용자가 실제로 입력한 메시지

Output Contract
- Markdown 답변인지
- JSON schema인지
- citation 필수인지
```

프롬프트 작성에서 중요한 것은 모델에게 "잘해줘"라고 부탁하는 것이 아니라, 입력과 출력의 계약을 분명히 주는 것이다.

## Structured Output

구조화 출력은 모델에게 JSON schema에 맞는 결과를 요구하는 방식이다.  
사용자에게 보여줄 자연어 답변은 Markdown으로 생성해도 되지만, 서버가 다음 단계에서 사용할 값은 JSON으로 받아야 안정적이다.

예를 들어 intent classifier는 아래처럼 구조화하는 것이 좋다.

```json
{
  "intent": "rag_question",
  "needs_rag": true,
  "needs_tool": false,
  "confidence": 0.87,
  "reason": "사용자가 과거 게시글 기반 답변을 요청함"
}
```

이런 출력은 다음 분기에서 바로 사용할 수 있다.

```text
needs_rag == true  -> Retriever 실행
needs_tool == true -> MCP tool 후보 선택
confidence < 0.5   -> 사용자에게 clarification 요청
```

### 구조화 출력이 필요한 곳

```text
Intent Classification
- 요청 유형 판단

Query Rewrite
- 검색어 후보 생성

Tool Planning
- tool 이름과 인자 결정

Safety Check
- 위험도와 차단 여부 판단

Answer Verification
- 답변이 근거를 사용했는지 점검

Auto Tagging
- 게시글 태그 후보 생성
```

## Function Calling

Function Calling은 모델이 직접 함수를 실행하는 것이 아니다.  
모델은 "이 함수를 이런 인자로 호출하면 좋겠다"는 구조화된 요청을 만들고, 실제 실행은 서버가 한다.

```text
LLM
-> call search_posts(query="FastAPI JWT 인증", limit=5)

Server
-> 실제 Python 함수 실행
-> 결과를 다시 LLM에게 전달
```

이 구분이 중요하다. 모델은 판단하고, 서버는 실행한다.  
따라서 서버는 tool 인자를 검증하고, 권한을 확인하고, 결과를 제한해서 다시 모델에게 넘겨야 한다.

### Function tool 설계 기준

좋은 tool은 작고 명확하다.

```text
좋은 예
- search_posts(query, tag_ids, limit)
- get_post(post_id)
- search_github_issues(repo, query, limit)
- summarize_file(file_id)

나쁜 예
- do_everything(user_request)
- run_external_api(raw_prompt)
- execute_code(command)
```

tool은 모델이 고르기 쉬워야 하고, 서버가 안전하게 검증할 수 있어야 한다.

## Streaming

AI 기능은 오래 걸린다.  
모델 답변 생성, RAG 검색, MCP tool 호출, 재검색, 검증이 모두 들어가면 일반 HTTP API처럼 한 번에 응답하기 어렵다.

그래서 사용자에게는 SSE 이벤트로 진행 상황을 보여주는 편이 좋다.

```text
agent.started
intent.classified
rag.query_rewritten
rag.search_started
rag.search_completed
mcp.tool_call_started
mcp.tool_call_completed
llm.answer_delta
agent.completed
agent.failed
```

프론트는 이 이벤트를 그대로 로그처럼 보여주지 않고, 사용자에게 자연스러운 문장으로 바꾼다.

```text
"질문 의도를 파악하고 있어요"
"관련 게시글을 찾고 있어요"
"외부 도구로 GitHub 이슈를 확인하고 있어요"
"답변을 작성하고 있어요"
```

## Token Budget

LLM에는 한 번에 넣을 수 있는 context 한계가 있다.  
RAG 결과, 대화 기록, tool 결과를 전부 넣으면 token이 금방 커지고 비용도 늘어난다.

따라서 context를 넣기 전에 예산을 정해야 한다.

```text
system instruction        1,000 tokens
recent conversation       2,000 tokens
RAG context               6,000 tokens
MCP tool output           3,000 tokens
answer budget             2,000 tokens
reserved safety margin    1,000 tokens
```

실제 값은 모델과 기능에 따라 달라지지만, 중요한 건 "되는 대로 다 넣기"를 피하는 것이다.

### Context 압축 전략

```text
최근 대화 우선
- 오래된 대화는 요약해서 넣기

RAG top-k 제한
- 검색 결과를 20개 넣기보다 좋은 5개만 넣기

Tool output 필드 제한
- 외부 API 응답 전체가 아니라 필요한 필드만 넣기

중복 context 제거
- 같은 게시글 chunk가 여러 번 들어가지 않게 하기

근거 없는 memory 배제
- 확실하지 않은 장기 memory는 답변 근거로 쓰지 않기
```

## LLM Runtime 인터페이스

Python에서는 구체 구현을 바로 여기저기서 import하지 말고, port/interface를 먼저 둔다.

```python
from typing import AsyncIterator, Protocol
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMResult(BaseModel):
    text: str
    usage: LLMUsage
    raw_response_id: str | None = None


class LLMClient(Protocol):
    async def generate_text(self, messages: list[LLMMessage]) -> LLMResult:
        ...

    async def stream_text(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        ...

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        schema: type[BaseModel],
    ) -> BaseModel:
        ...
```

이렇게 해두면 OpenAI를 쓰다가 다른 provider로 바꿔도 application layer는 크게 바뀌지 않는다.

## 실패 처리

LLM 호출은 실패할 수 있다.

```text
API timeout
rate limit
invalid structured output
tool call arguments parsing failure
context too long
model refusal
network error
```

실패 처리는 기능별로 다르게 해야 한다.

```text
timeout
- 재시도 가능
- 사용자에게 "조금 지연되고 있다" 이벤트 전달

rate limit
- 즉시 무한 재시도 금지
- queue 또는 cooldown 필요

invalid JSON
- structured output을 쓰거나 1회 repair 시도

context too long
- context 압축 후 재시도

tool argument invalid
- 서버에서 reject하고 모델에게 관찰 결과로 전달
```

## LLM Runtime에서 저장할 로그

```text
llm_call_id
agent_run_id
provider
model
request_type
input_summary
output_summary
input_tokens
output_tokens
latency_ms
error_code
created_at
```

원문 prompt 전체를 무조건 저장하는 것은 조심해야 한다. 개인정보, API 결과, 비밀값이 들어갈 수 있기 때문이다.  
운영에서는 원문 저장 여부와 마스킹 정책을 따로 정해야 한다.

