# Agent Ask Flow

이 문서는 사용자가 채팅창에 질문을 입력한 뒤, 상위 agent graph가 답변 기준을 추론하고, 필요하면 RAG graph를 호출해서 답변을 만드는 흐름을 실제 코드에 매핑해서 설명한다.

먼저 목표로 삼는 큰 사고 사이클은 아래와 같다.

```text
사용자 입력
-> 채팅 세션과 메시지로 저장
-> 사용자 요청 의도 판단
-> 답변 기준 레포/브랜치/커밋 추론
-> 필요한 도구 또는 하위 graph 선택
-> RAG 답변 / 게시글 작업 / MCP 작업 / 직접 답변 중 하나 실행
-> 실행 결과와 추론 결과를 프론트에 반환
-> 사용자가 이어서 대화하면 다시 같은 사이클 반복
```

현재 코드의 `/agent/chat`은 이 사이클 전체를 모두 구현한 최종 agent workflow는 아니다. 지금 구현은 아래 흐름에 더 가깝다.

```text
사용자 채팅 입력
-> ChatSendMessageRequestDTO
-> send_chat_message()
-> AgentChatService.send_message(db, session_id, request)
-> 사용자 메시지를 ChatStore에 저장
-> TurnQueue에 ChatTurn 추가
-> GraphAgentResponder.answer(...)
-> AgentGraph.run(...)
-> SQL에서 최근 RAG 분석 run 목록 조회
-> 질문 문자열에서 레포/브랜치 최소 추론
-> 추론 성공 시 RagAnswerService.answer(...) 호출
-> RagAnswerGraph.run(...) 내부 RAG 흐름 실행
-> assistant 메시지 저장
-> ChatSendMessageResponseDTO로 메시지 목록과 inferred_repository_refs 반환
```

즉 현재 구현된 것은 `상위 agent graph가 RAG graph를 노드처럼 호출하는 최소 구조`다. LLM planner, MCP action, 게시글 작성/수정 action, 사용자 승인 workflow는 확장 포인트로 남아 있다.

## 현재 구현과 구조만 있는 흐름

아래 표는 목표 사이클을 기준으로 현재 코드 상태를 나눈 것이다.

| 단계 | 현재 상태 | 코드 위치 |
| --- | --- | --- |
| 사용자 입력 | 구현됨 | `backend/app/agent/api/router.py`의 `send_chat_message()` |
| 입력을 요청 DTO로 받기 | 구현됨 | `backend/app/agent/api/schema.py`의 `ChatSendMessageRequestDTO` |
| 채팅 세션 조회 | 구현됨 | `AgentChatService.require_session()` |
| 사용자 메시지 저장 | 구현됨 | `AgentChatService.send_message()`와 `ChatStore.append_message()` |
| turn 큐 처리 | 구현됨 | `TurnQueue`, `AgentChatService.run_queue()` |
| 요청 의도 판단 | 구조만 있음 | 현재 `AgentGraph.plan_turn()`은 LLM 판단이 아니라 레포/브랜치 문자열 최소 추론만 한다. |
| 답변 기준 추론 | 일부 구현됨 | `infer_repository_refs()`가 최근 RAG run 목록에서 레포/브랜치를 추론한다. |
| 추론 결과 프론트 반환 | 구현됨 | `ChatSendMessageResponseDTO.inferred_repository_refs` |
| RAG graph 호출 | 구현됨 | `AgentGraph.call_rag_answer()`가 `RagAnswerService.answer()`를 호출한다. |
| MCP action 선택 | 구조만 있음 | 아직 MCP node나 action executor는 없다. |
| 게시글/보드 action 선택 | 구조만 있음 | board service는 있지만 agent graph node로 연결되어 있지 않다. |
| 사용자 승인 흐름 | 구조만 있음 | action 실행 전 확인/승인 DTO와 graph node가 아직 없다. |
| assistant 메시지 저장 | 구현됨 | `AgentChatService.run_queue()` |
| 최종 응답 반환 | 구현됨 | `ChatSendMessageResponseDTO` |

여기서 `구조만 있음`은 나중에 끼워 넣을 위치가 있다는 뜻이다. 현재 코드는 agent의 외형, 세션 흐름, RAG graph 호출 구조를 먼저 만든 상태다.

## 실제 파일 순서

사용자가 채팅창에 질문을 입력해서 답변을 받는 현재 코드 흐름은 아래 순서로 읽는다.

```text
router.py
  send_chat_message()
    ↓
schema.py
  ChatSendMessageRequestDTO
    ↓
chat_service.py
  send_message(db, session_id, request)
    ↓
domain/chat.py
  ChatTurn, TurnQueue
    ↓
graph_responder.py
  GraphAgentResponder.answer(...)
    ↓
agent_graph.py
  AgentGraph.run(...)
    ↓
agent_graph.py
  collect_repository_context()
    ↓
sql_repository.py
  list_runs(db, limit=50)
    ↓
agent_graph.py
  plan_turn()
    ↓
agent_graph.py
  infer_repository_refs()
    ↓
agent_graph.py
  call_rag_answer()
    ↓
answer_service.py
  RagAnswerService.answer(db, request)
    ↓
answer_graph.py
  RagAnswerGraph.run(request, index_run)
    ↓
chat_service.py
  assistant 메시지 저장
    ↓
schema.py
  ChatSendMessageResponseDTO
    ↓
router.py
  클라이언트에게 응답
```

## 1. 사용자 입력

사용자는 프론트 채팅창에서 메시지를 보낸다.

예시 요청은 이런 모양이다.

```http
POST /agent/chat/sessions/{session_id}/messages
Content-Type: application/json
```

```json
{
  "content": "Jungle-303-04/warm-up minjeong 브랜치 기준으로 RAG 흐름 설명해줘"
}
```

이 요청에서 중요한 값은 하나다.

```text
content
  사용자가 agent에게 보낸 자연어 입력이다.
  현재는 이 문자열에서 레포 이름과 브랜치를 최소 추론한다.
  나중에는 이 문자열을 LLM planner가 읽고 의도, 필요한 도구, 승인 필요 여부까지 판단한다.
```

현재 HTTP 입구는 `backend/app/agent/api/router.py`의 `send_chat_message()` 함수다.

## 2. 입력을 요청 DTO로 받기

파일:

```text
backend/app/agent/api/schema.py
```

관련 코드:

```python
class ChatSendMessageRequestDTO(BaseModel):
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("content must not be empty")
        return content
```

FastAPI는 클라이언트가 보낸 JSON body를 보고 `ChatSendMessageRequestDTO` 객체를 만든다.

```text
JSON body
-> ChatSendMessageRequestDTO(content)
```

`content`가 비어 있으면 요청은 거부된다.

## 3. 라우터가 DB 세션과 ChatService를 연결한다

파일:

```text
backend/app/agent/api/router.py
```

관련 흐름:

```python
def send_chat_message(
    session_id: str,
    request: ChatSendMessageRequestDTO,
    db: Session = Depends(get_session),
    chat_service: AgentChatUseCase = Depends(Provide[AppContainer.agent_chat_service]),
) -> ChatSendMessageResponseDTO:
    return chat_service.send_message(db, session_id, request)
```

여기서 `db`가 중요한 이유는 agent graph가 RAG 분석 run을 SQL에서 조회해야 하기 때문이다.

이전의 단순 echo responder는 DB가 필요 없었다. 하지만 지금은 agent graph 안에서 아래 흐름이 실행된다.

```text
SQL에서 최근 RAG 분석 run 조회
-> 질문에 맞는 run 추론
-> RagAnswerService.answer(db, request)
```

그래서 `/agent/chat` 라우터도 DB 세션을 받아 service로 넘긴다.

## 4. ChatService가 사용자 메시지를 저장하고 turn을 만든다

파일:

```text
backend/app/agent/service/chat_service.py
```

핵심 흐름:

```python
session = self.require_session(session_id)
user_message = self.store.append_message(
    session_id=session.id,
    role=USER_ROLE,
    content=request.content,
)

queue = TurnQueue()
queue.enqueue(
    ChatTurn(
        session_id=session.id,
        user_message_id=user_message.id,
        user_input=user_message.content,
    )
)
processed_turns, turn_result = self.run_queue(db, session, queue)
```

`ChatService`는 agent의 판단을 직접 하지 않는다.

역할은 아래에 가깝다.

```text
채팅방 존재 확인
-> 사용자 메시지 저장
-> 처리할 turn 생성
-> responder에 turn 전달
-> assistant 메시지 저장
-> API 응답 DTO 생성
```

## 5. TurnQueue는 한 번의 사용자 입력을 작업 단위로 만든다

파일:

```text
backend/app/agent/domain/chat.py
```

관련 객체:

```python
@dataclass(frozen=True)
class ChatTurn:
    session_id: str
    user_message_id: str
    user_input: str
```

`ChatTurn`은 agent가 처리해야 하는 사용자 입력 한 건이다.

`TurnQueue`를 둔 이유는 나중에 agent가 후속 작업을 이어서 넣을 수 있게 하기 위해서다.

예를 들면 미래에는 이런 흐름이 가능하다.

```text
사용자 입력 turn
-> agent가 "레포 분석 필요" 판단
-> 레포 분석 action turn enqueue
-> 분석 완료 후 "요약 답변" turn enqueue
```

현재는 사용자 입력 한 건만 처리한다.

## 6. GraphAgentResponder가 상위 AgentGraph를 호출한다

파일:

```text
backend/app/agent/service/graph_responder.py
```

관련 코드:

```python
class GraphAgentResponder:
    def answer(
        self,
        db: Session,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> AgentTurnResult:
        return self.agent_graph.run(
            db=db,
            session=session,
            messages=messages,
            turn=turn,
        )
```

`GraphAgentResponder`는 어댑터다.

`AgentChatService`는 responder가 어떤 방식으로 답변을 만드는지 몰라도 된다.

```text
AgentChatService
-> responder.answer(...)
```

이 계약만 알고 있다.

현재 컨테이너에서는 responder가 `GraphAgentResponder`로 연결되어 있다.

```text
GraphAgentResponder
-> AgentGraph
```

## 7. AgentGraph는 큰 AI 흐름의 중심이다

파일:

```text
backend/app/agent/service/agent_graph.py
```

현재 graph 구조는 아래와 같다.

```text
collect_repository_context
-> plan_turn
   -> call_rag_answer
   -> build_direct_answer
```

코드로 보면:

```python
graph.add_node("collect_repository_context", self.collect_repository_context)
graph.add_node("plan_turn", self.plan_turn)
graph.add_node("call_rag_answer", self.call_rag_answer)
graph.add_node("build_direct_answer", self.build_direct_answer)

graph.set_entry_point("collect_repository_context")
graph.add_edge("collect_repository_context", "plan_turn")
graph.add_conditional_edges(
    "plan_turn",
    self.route_after_plan,
    {
        RAG_ANSWER_ROUTE: "call_rag_answer",
        DIRECT_ANSWER_ROUTE: "build_direct_answer",
    },
)
```

이 graph는 아직 완성형 AI agent가 아니다.

현재 역할은 아래에 가깝다.

```text
최근 RAG 분석 run을 가져온다.
사용자 질문에서 레포/브랜치를 추론한다.
추론 성공 시 RAG 답변 graph를 호출한다.
추론 실패 시 안내 답변을 만든다.
```

## 8. collect_repository_context가 최근 분석 run을 가져온다

파일:

```text
backend/app/agent/service/agent_graph.py
```

관련 코드:

```python
def collect_repository_context(self, state: AgentGraphState) -> AgentGraphState:
    return {
        "latest_runs": [
            run
            for run in self.sql_repository.list_runs(state["db"], limit=50)
            if run.repository_full_name
        ],
    }
```

`latest_runs`는 agent가 답변 기준을 고를 때 참고하는 후보 목록이다.

여기서 `repository_full_name`이 없는 run은 제외한다.

왜냐하면 직접 파일 목록을 넘겨 저장한 개발용 run은 어떤 GitHub 레포 기준인지 알 수 없고, 사용자가 자연어로 선택하기 어렵기 때문이다.

## 9. plan_turn이 질문에서 레포/브랜치를 추론한다

파일:

```text
backend/app/agent/service/agent_graph.py
```

관련 코드:

```python
inferred_repository_refs = infer_repository_refs(
    user_input=state["turn"].user_input,
    runs=state.get("latest_runs", []),
)
```

현재 추론은 LLM이 아니다.

지금은 최소 규칙 기반 추론이다.

```text
owner/repo 전체 이름이 질문에 있는가?
repo 이름만 질문에 있는가?
branch 이름이 질문에 있는가?
레포가 하나뿐이면 그 레포를 기본값으로 쓸 수 있는가?
```

점수는 이런 식으로 계산된다.

```text
full repository + branch -> 60
repo name + branch       -> 50
full repository          -> 40
repo name                -> 30
branch only              -> 20
```

현재 이 노드는 나중에 LLM planner로 바꿀 자리다.

미래의 planner는 아래까지 판단할 수 있다.

```text
질문 답변인가?
게시글 작성인가?
회의록 정리인가?
레포 분석 실행이 필요한가?
MCP action이 필요한가?
사용자 승인이 필요한가?
답변 기준 레포가 모호해서 되물어야 하는가?
```

## 10. inferred_repository_refs는 프론트로도 내려간다

파일:

```text
backend/app/agent/api/schema.py
backend/app/agent/service/chat_service.py
```

응답 DTO:

```python
class AgentInferredRepositoryRefDTO(BaseModel):
    run_id: int | None = None
    repository_full_name: str
    branch: str | None = None
    commit_sha: str | None = None


class ChatSendMessageResponseDTO(ChatSessionDetailResponseDTO):
    processed_turns: int
    inferred_repository_refs: list[AgentInferredRepositoryRefDTO] | None = None
```

추론에 성공하면 응답은 이런 모양이 될 수 있다.

```json
{
  "processed_turns": 1,
  "inferred_repository_refs": [
    {
      "run_id": 12,
      "repository_full_name": "Jungle-303-04/warm-up",
      "branch": "minjeong",
      "commit_sha": "842d495..."
    }
  ]
}
```

추론에 실패하면 `null`이다.

```json
{
  "processed_turns": 1,
  "inferred_repository_refs": null
}
```

프론트는 이 값을 보고 상단의 답변 대상 UI를 갱신할 수 있다.

```text
agent가 추론한 레포가 있다
-> 상단 선택 chip/check 상태 갱신

agent가 추론하지 못했다
-> "답변 대상을 찾지 못했습니다" 안내
```

중요한 점은 이 추론이 매 turn 반복될 수 있다는 것이다.

```text
첫 질문: warm-up main 기준으로 설명해줘
-> inferred_repository_refs = [warm-up/main]

다음 질문: 이번엔 minjeong 브랜치랑 비교해줘
-> inferred_repository_refs = [warm-up/minjeong]

다음 질문: project-a랑 warm-up 둘 다 봐줘
-> inferred_repository_refs = [project-a/..., warm-up/...]
```

현재 최소 추론은 여러 레포를 완벽히 처리하지는 못하지만, DTO와 graph state는 여러 개를 담을 수 있게 열려 있다.

## 11. call_rag_answer가 RAG graph를 노드처럼 호출한다

파일:

```text
backend/app/agent/service/agent_graph.py
```

관련 코드:

```python
rag_request = RagAskRequestDTO(
    question=state["turn"].user_input,
    repository_refs=[
        to_rag_repository_ref(ref)
        for ref in state.get("inferred_repository_refs") or []
    ],
    limit=5,
)
rag_response = self.rag_answer_service.answer(state["db"], rag_request)
```

여기서 중요한 점은 `AgentGraph`가 `RagAnswerGraph`를 직접 import해서 호출하지 않는다는 것이다.

호출 구조는 이렇다.

```text
AgentGraph
-> RagAnswerService.answer(db, request)
-> RagAnswerService가 SQL에서 run 확정
-> RagAnswerGraph.run(request, index_run)
```

즉 상위 agent graph 입장에서는 RAG 답변 기능 전체가 하나의 노드처럼 보인다.

이 구조 덕분에 나중에 아래 노드를 추가하기 쉽다.

```text
call_mcp_action
call_board_action
ask_user_confirmation
summarize_chat_history
rewrite_question
```

## 12. RAG graph 내부 흐름은 rag_ask_flow.md를 따른다

`AgentGraph.call_rag_answer()` 이후의 실제 RAG 검색/LLM 답변 흐름은 `docs/rag_ask_flow.md`의 내용과 같다.

간단히 줄이면:

```text
RagAnswerService.answer()
-> SQL에서 repository_full_name / branch / commit_sha 기준 index_run 조회
-> RagAnswerGraph.run()
-> vector DB 검색
-> LLM에게 질문 + 근거 전달
-> RagAskResponseDTO 반환
```

현재 RAG graph는 아직 SQL keyword 검색과 vector 검색 결과 결합을 하지 않는다.

그래서 상위 agent graph가 생겼다고 해서 RAG 품질 문제가 자동으로 해결되는 것은 아니다.

다음 단계에서는 아래 둘을 따로 개선해야 한다.

```text
AgentGraph
  의도 판단, 도구 선택, 사용자 승인, MCP action 담당

RagAnswerGraph 또는 EvidenceRetriever
  SQL keyword 검색, vector 검색, 검색 결과 결합 담당
```

## 13. build_direct_answer는 추론 실패 안내를 만든다

파일:

```text
backend/app/agent/service/agent_graph.py
```

관련 흐름:

```python
if not latest_runs:
    return {
        "final_answer": (
            "아직 답변에 사용할 레포지토리 분석 결과가 없습니다. "
            "먼저 레포지토리를 등록하고 분석해 주세요."
        ),
    }
```

분석 run이 아예 없으면 먼저 레포지토리를 분석하라고 안내한다.

분석 run은 있는데 질문에서 어떤 레포인지 못 찾으면 예시를 보여준다.

```text
어떤 레포지토리 기준으로 답할지 아직 고르지 못했습니다.
질문에 레포지토리 이름이나 브랜치를 함께 적어 주세요.
```

이 상태의 응답에는 `inferred_repository_refs`가 `null`로 내려간다.

## 14. ChatService가 assistant 메시지를 저장하고 응답 DTO를 만든다

파일:

```text
backend/app/agent/service/chat_service.py
```

관련 코드:

```python
turn_result = self.responder.answer(...)
self.store.append_message(
    session_id=session.id,
    role=ASSISTANT_ROLE,
    content=turn_result.content,
)
```

저장소에는 assistant의 답변 문자열만 저장한다.

추론 결과는 메시지 본문에 섞지 않고, API 응답의 별도 필드로 내려준다.

```python
ChatSendMessageResponseDTO(
    session=...,
    messages=...,
    processed_turns=processed_turns,
    inferred_repository_refs=...
)
```

이렇게 나눈 이유는 프론트가 답변 텍스트와 UI 상태 갱신 정보를 다르게 다뤄야 하기 때문이다.

```text
messages
  채팅 말풍선 렌더링용

inferred_repository_refs
  답변 대상 chip/check 갱신용
```

## 15. Container가 AgentGraph를 조립한다

파일:

```text
backend/app/container.py
```

관련 구조:

```python
agent_graph = providers.Singleton(
    AgentGraph,
    rag_answer_service=rag_answer_service,
    sql_repository=rag_sql_repository,
)
agent_responder = providers.Singleton(
    GraphAgentResponder,
    agent_graph=agent_graph,
)
agent_chat_service = providers.Singleton(
    AgentChatService,
    store=agent_chat_store,
    responder=agent_responder,
)
```

즉 현재 `/agent/chat`은 더 이상 기본 echo responder를 쓰지 않는다.

흐름은 아래처럼 조립된다.

```text
AgentChatService
-> GraphAgentResponder
-> AgentGraph
-> RagAnswerService
-> RagAnswerGraph
```

`EchoAgentResponder` 파일은 남아 있지만, 기본 컨테이너 연결에서는 빠져 있다. 나중에 테스트용이나 fallback용으로 쓸 수 있다.

## 현재 AgentGraph를 한 줄로 말하면

현재 `/agent/chat`은 아래 역할을 한다.

```text
채팅 메시지를 저장하고,
최근 RAG 분석 run 목록을 보고,
질문에서 답변 기준 레포/브랜치를 최소 추론하고,
추론에 성공하면 기존 RAG 답변 graph를 호출하고,
추론 결과를 프론트에 함께 내려준다.
```

아직 완성되지 않은 부분은 아래와 같다.

```text
LLM planner
SQL/vector evidence fusion
게시글 작성/수정 action
회의록 정리/태그 추천
MCP tool call
사용자 승인 workflow
장기 채팅 메모리
SQL 기반 채팅 세션 저장
```

## 이후 확장할 때의 자연스러운 방향

### 1. LLM planner 추가

현재 `plan_turn()`은 문자열 규칙 기반이다.

나중에는 이 노드를 LLM planner로 바꾸는 것이 자연스럽다.

```text
plan_turn
-> LLM이 JSON으로 의도 반환
```

예시:

```json
{
  "intent": "rag_answer",
  "repository_refs": [
    {
      "repository_full_name": "Jungle-303-04/warm-up",
      "branch": "minjeong"
    }
  ],
  "needs_confirmation": false
}
```

### 2. MCP action node 추가

MCP나 GitHub 작업을 붙이면 graph에 새 node가 생긴다.

```text
plan_turn
-> call_rag_answer
-> call_mcp_action
-> ask_user_confirmation
```

중요한 점은 action은 바로 실행하면 안 된다는 것이다.

대부분의 외부 실행은 아래 흐름이 필요하다.

```text
agent가 실행 계획 제안
-> 사용자 승인
-> 실제 MCP/API 호출
-> 결과 보고
```

### 3. Board action node 추가

AI 게시글 초안, 회의록 정리, 태그 추천도 agent graph에 붙일 수 있다.

```text
plan_turn
-> draft_board_post
-> suggest_tags
-> ask_user_confirmation
-> create_board
```

현재 board API는 이미 있으므로, agent가 board service를 호출하는 node를 만들 수 있다.

### 4. EvidenceRetriever 분리

RAG 품질을 높이려면 `RagAnswerGraph` 안에서 SQL keyword 검색과 vector 검색을 합쳐야 한다.

다만 `answer_graph.py`가 너무 커지지 않게 하려면 별도 `EvidenceRetriever`를 두는 편이 좋다.

```text
RagAnswerGraph
-> EvidenceRetriever.retrieve()
   -> SQL keyword search
   -> vector search
   -> fusion
-> LLM answer
```

이건 agent graph와 별개로 RAG 내부 품질 개선 작업이다.

## 공부 순서

agent 흐름을 처음 읽을 때는 아래 순서가 좋다.

```text
1. backend/app/agent/api/router.py
   HTTP 요청이 어디로 들어오는지 본다.

2. backend/app/agent/api/schema.py
   요청/응답 DTO를 본다.

3. backend/app/agent/service/chat_service.py
   메시지 저장과 turn 처리 흐름을 본다.

4. backend/app/agent/domain/chat.py
   ChatSession, ChatMessage, ChatTurn, AgentTurnResult를 본다.

5. backend/app/agent/service/graph_responder.py
   service와 graph 사이 어댑터를 본다.

6. backend/app/agent/service/agent_graph.py
   상위 agent graph 흐름을 본다.

7. backend/app/rag/service/answer_service.py
   agent가 호출한 RAG use case를 본다.

8. backend/app/rag/service/answer_graph.py
   실제 RAG LangGraph 흐름을 본다.

9. backend/app/container.py
   이 객체들이 어떻게 조립되는지 본다.
```

## 요약

현재 agent ask 흐름은 완성형 AI agent는 아니지만, 큰 방향은 잡혀 있다.

```text
/agent/chat
-> AgentChatService
-> AgentGraph
-> RagAnswerService
-> RagAnswerGraph
```

이 구조의 핵심은 두 가지다.

첫째, 프론트가 직접 RAG 기준을 완벽히 정하지 않아도, agent가 대화에서 답변 기준을 추론할 수 있는 자리가 생겼다.

둘째, RAG는 상위 agent graph의 하위 node처럼 호출된다. 그래서 나중에 MCP, 게시글 action, 사용자 승인 흐름을 같은 graph에 붙일 수 있다.

