# RAG Ask Flow

이 문서는 사용자가 프롬프트를 입력한 뒤, 저장된 RAG 근거를 검색하고, LLM 답변을 받아 사용자에게 돌려주는 흐름을 실제 코드에 매핑해서 설명한다.

먼저 목표로 삼는 사고 사이클은 아래와 같다.

```text
사용자 입력
-> 입력을 요청 DTO로 받기
-> 어떤 작업인지 판단
-> 검색 계획 세우기
-> SQL 검색 / Vector 검색
-> 검색 결과 결합
-> LLM에게 질문 + 근거 전달
-> LLM 결과 해석
-> 사용자에게 답변하거나, 다음 로직 실행
```

현재 코드의 `/rag/ask`는 이 사이클 전체를 모두 구현한 최종 agent workflow는 아니다. 지금 구현은 아래 흐름에 더 가깝다.

```text
사용자 질문
-> RagAskRequestDTO
-> ask_repository_rag()
-> RagAnswerService.answer()
-> Vector 검색
-> 검색 결과 row 변환
-> LLM에게 질문 + Vector 근거 전달
-> RagAskResponseDTO로 사용자에게 반환
```

즉 현재 구현된 것은 `Vector 검색 기반 RAG 답변`이다. SQL 검색, SQL/Vector 결과 결합, 작업 판단, 다음 로직 실행은 확장 포인트로 남아 있다.

## 현재 구현과 구조만 있는 흐름

아래 표는 목표 사이클을 기준으로 현재 코드 상태를 나눈 것이다.

| 단계 | 현재 상태 | 코드 위치 |
| --- | --- | --- |
| 사용자 입력 | 구현됨 | `backend/app/rag/api/router.py`의 `ask_repository_rag()` |
| 입력을 요청 DTO로 받기 | 구현됨 | `backend/app/rag/api/schema.py`의 `RagAskRequestDTO` |
| 어떤 작업인지 판단 | 구조만 있음 | `/rag/ask`로 들어온 요청은 무조건 답변 생성으로 처리한다. 별도 intent 판단 구현은 아직 없다. |
| 검색 계획 세우기 | 구조만 있음 | `RagAnswerService.answer()`가 vector 검색 하나만 고정 실행한다. planner 객체는 아직 없다. |
| SQL 검색 | 일부 구현됨, ask 흐름에는 미연결 | `RagSqlRepository.search_chunks_by_keyword()` 같은 SQL 검색 기능은 있지만 `/rag/ask`에는 아직 연결되지 않았다. |
| Vector 검색 | 구현됨 | `RagVectorRepository.search()` |
| 검색 결과 결합 | 구조만 있음 | `VectorResultRow`로 vector 결과를 row화하지만 SQL/Vector fusion 로직은 아직 없다. |
| LLM에게 질문 + 근거 전달 | 구현됨 | `RagLlm.answer_with_evidence()`, `PromptBuilder`, `EvidenceFormatter` |
| LLM 결과 해석 | 단순 구현 | `OpenAIGenerator.generate()`가 텍스트만 반환한다. 구조화 파싱은 아직 없다. |
| 사용자에게 답변 | 구현됨 | `RagAskResponseDTO` |
| 다음 로직 실행 | 구조만 있음 | action executor나 agent router는 아직 `/rag/ask` 흐름에 없다. |

여기서 `구조만 있음`은 코드가 아예 없다는 뜻만은 아니다. DTO, interface, service 분리처럼 나중에 끼워 넣을 자리는 있지만, 실제 분기나 처리 구현은 아직 없다는 뜻이다.

## 실제 파일 순서

사용자가 프롬프트를 입력해서 답변을 받는 현재 코드 흐름은 아래 순서로 읽는다.

```text
router.py
  ask_repository_rag()
    ↓
schema.py
  RagAskRequestDTO
    ↓
container.py
  rag_answer_service 주입
    ↓
answer_service.py
  answer(request)
    ↓
vector_repository.py
  search(question, limit, run_id)
    ↓
embedding.py
  embed_text(question)
    ↓
vector_result.py
  검색 결과 row 구조
    ↓
llm_client.py
  검색 근거로 LLM 답변 생성
    ↓
answer_service.py
  RagAskResponseDTO로 포장
    ↓
router.py
  클라이언트에게 응답
```

## 1. 사용자 입력

사용자는 프론트나 Postman 같은 클라이언트에서 질문을 보낸다.

예시 요청은 이런 모양이다.

```http
POST /rag/ask
Content-Type: application/json
Cookie: warm_up_auth_token=...
```

```json
{
  "question": "이 레포에서 RAG 인덱싱 흐름을 설명해줘",
  "run_id": 3,
  "limit": 5
}
```

이 요청에서 중요한 값은 세 가지다.

```text
question
  사용자가 LLM에게 묻고 싶은 질문이다.

run_id
  어떤 인덱싱 실행 결과 안에서만 검색할지 제한하는 값이다.
  없으면 전체 vector collection에서 검색할 수 있다.

limit
  vector DB에서 최대 몇 개의 관련 chunk를 가져올지 정하는 값이다.
```

현재 코드에서 사용자 입력을 받는 HTTP 입구는 `backend/app/rag/api/router.py`의 `ask_repository_rag()` 함수다.

## 2. 입력을 요청 DTO로 받기

파일:

```text
backend/app/rag/api/schema.py
```

관련 코드:

```python
class RagAskRequestDTO(BaseModel):
    question: str
    run_id: int | None = Field(default=None, ge=1)
    limit: int = Field(default=5, ge=1, le=MAX_SEARCH_LIMIT)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question must not be empty")
        return question
```

FastAPI는 클라이언트가 보낸 JSON body를 보고 `RagAskRequestDTO` 객체를 만든다.

```text
JSON body
-> RagAskRequestDTO(question, run_id, limit)
```

이 DTO가 하는 일은 단순히 값을 담는 것만이 아니다.

`question`은 앞뒤 공백을 제거하고, 빈 문자열이면 거부한다.

`run_id`는 있으면 1 이상이어야 한다.

`limit`은 기본값 5이고, 1 이상 `MAX_SEARCH_LIMIT` 이하로 제한된다.

즉 이 단계는 사용자 입력을 코드에서 신뢰할 수 있는 형태로 바꾸는 단계다.

목표 사이클에서 이 부분에 해당한다.

```text
사용자 입력
-> 입력을 요청 DTO로 받기
```

## 3. 라우터에서 요청을 받기

파일:

```text
backend/app/rag/api/router.py
```

관련 함수:

```python
@rag.post(
    "/ask",
    tags=["rag"],
    response_model=RagAskResponseDTO,
)
@inject
def ask_repository_rag(
    request: RagAskRequestDTO,
    authorization: str | None = Header(default=None),
    auth_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_session),
    auth_service: AuthServicePort = Depends(Provide[AppContainer.auth_service]),
    answer_service: AnswerUseCase = Depends(Provide[AppContainer.rag_answer_service]),
) -> RagAskResponseDTO:
    """저장된 RAG 근거를 검색하고 LLM 답변과 출처를 함께 반환한다."""

    try:
        resolve_github_account(db, auth_service, authorization, auth_cookie)
        return answer_service.answer(request)
    except AuthTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
```

이 함수는 `/rag/ask` API의 입구다.

`@rag.post("/ask")`는 이 함수를 POST API로 등록한다.

`response_model=RagAskResponseDTO`는 이 API가 최종적으로 `RagAskResponseDTO` 모양의 응답을 반환한다고 FastAPI에 알려준다.

`@inject`는 `Provide[AppContainer...]`로 표시된 의존성을 실제 객체로 바꿔 넣는 역할을 한다.

여기서 함수가 받는 값은 크게 두 종류다.

```text
클라이언트 요청에서 오는 값
  request
  authorization
  auth_cookie

서버 내부에서 주입되는 값
  db
  auth_service
  answer_service
```

`request`는 사용자의 질문이다.

`authorization`, `auth_cookie`는 로그인 여부를 확인하기 위한 인증 토큰이다.

`db`는 DB 세션이다.

`auth_service`는 인증된 GitHub 계정인지 확인하는 서비스다.

`answer_service`가 실제 RAG 답변 생성을 담당하는 서비스다.

라우터 함수 안에서 가장 중요한 줄은 이 두 줄이다.

```python
resolve_github_account(db, auth_service, authorization, auth_cookie)
return answer_service.answer(request)
```

첫 번째 줄은 인증 확인이다. 로그인된 사용자만 RAG ask를 실행하게 막는다.

두 번째 줄은 실제 RAG 답변 생성으로 넘어가는 부분이다.

목표 사이클 기준으로 보면 현재 라우터는 아직 복잡한 작업 판단을 하지 않는다. 인증만 확인하고, 모든 `/rag/ask` 요청을 `answer_service.answer()`로 보낸다.

```text
입력을 요청 DTO로 받기
-> 어떤 작업인지 판단
```

현재 구현에서 `어떤 작업인지 판단`은 사실상 고정되어 있다.

```text
/rag/ask로 들어온 요청은 RAG 답변 요청이다.
```

나중에 agent workflow로 확장하면 이 지점에서 `질문 답변`, `이슈 생성`, `코드 분석`, `보드 업데이트` 같은 의도를 나눌 수 있다.

## 4. AppContainer가 Answer Service를 조립한다

파일:

```text
backend/app/container.py
```

관련 코드:

```python
rag_vector_repository = providers.Singleton(
    RagVectorRepository,
    embedding_service=rag_embedding_service,
)

rag_evidence_formatter = providers.Singleton(EvidenceFormatter)
rag_prompt_builder = providers.Singleton(
    PromptBuilder,
    evidence_formatter=rag_evidence_formatter,
)
rag_text_generator = providers.Singleton(OpenAIGenerator)
rag_llm_client = providers.Singleton(
    RagLlm,
    prompt_builder=rag_prompt_builder,
    text_generator=rag_text_generator,
)
rag_answer_service = providers.Singleton(
    RagAnswerService,
    vector_repository=rag_vector_repository,
    llm_client=rag_llm_client,
)
```

`RagAnswerService`는 혼자 모든 일을 하지 않는다. 필요한 부품을 생성자에서 받는다.

```text
RagAnswerService
  vector_repository
  llm_client
```

`vector_repository`는 vector DB 검색 담당이다.

`llm_client`는 검색된 근거를 LLM에게 전달하고 답변을 받는 담당이다.

`@inject`와 `Depends(Provide[AppContainer.rag_answer_service])`는 이 컨테이너 설정을 보고 `ask_repository_rag()` 함수에 `answer_service`를 넣어준다.

이 단계의 핵심은 조립이다.

```text
router는 직접 RagAnswerService(...)를 만들지 않는다.
AppContainer가 필요한 하위 객체까지 조립해서 주입한다.
```

목표 사이클에서 말한 `흐름 만들기`, `인터페이스화`, `조립 가능한 형태`는 이 레이어와 관련이 깊다.

## 5. Answer Service가 검색 계획을 실행한다

파일:

```text
backend/app/rag/service/answer_service.py
```

관련 코드:

```python
class RagAnswerService:
    """벡터 검색으로 근거를 찾고, 그 근거만 LLM에 넘겨 답변을 만든다."""

    def __init__(
        self,
        vector_repository: VectorStore,
        llm_client: LlmClient,
    ) -> None:
        self.vector_repository = vector_repository
        self.llm_client = llm_client

    def answer(self, request: RagAskRequestDTO) -> RagAskResponseDTO:
        """질문과 선택 run_id로 관련 청크를 찾고 출처 목록과 함께 답변한다."""

        search_result = self.vector_repository.search(
            query=request.question,
            limit=request.limit,
            run_id=request.run_id,
        )
        rows = parse_vector_result(search_result)
```

여기서 현재 구현된 검색 계획은 단순하다.

```text
질문을 vector 검색한다.
run_id가 있으면 해당 run_id 안에서만 찾는다.
limit 개수만큼 가져온다.
```

이 단계가 목표 사이클의 이 부분이다.

```text
검색 계획 세우기
-> SQL 검색 / Vector 검색
```

현재는 SQL 검색 없이 vector 검색만 한다.

코드에서는 아래 줄이 검색 실행이다.

```python
search_result = self.vector_repository.search(
    query=request.question,
    limit=request.limit,
    run_id=request.run_id,
)
```

`request.question`은 사용자의 프롬프트다.

`request.limit`은 가져올 근거 chunk 개수다.

`request.run_id`는 특정 인덱싱 실행 결과로 검색 범위를 좁히는 값이다.

## 6. Vector Repository가 실제 Vector DB를 검색한다

파일:

```text
backend/app/rag/external/vector_repository.py
```

관련 코드:

```python
def search(self, query: str, limit: int = 5, run_id: int | None = None) -> dict:
    """질문을 embedding으로 바꿔 유사 청크를 찾고, run_id가 있으면 범위를 제한한다."""

    query_arguments = {
        "query_embeddings": [self.embedding_service.embed_text(query)],
        "n_results": limit,
    }
    if run_id is not None:
        query_arguments["where"] = {"run_id": run_id}

    return self.collection.query(**query_arguments)
```

여기서 하는 일은 세 가지다.

첫째, 사용자의 질문 문자열을 embedding vector로 바꾼다.

```python
self.embedding_service.embed_text(query)
```

둘째, Chroma에 몇 개를 검색할지 알려준다.

```python
"n_results": limit
```

셋째, `run_id`가 있으면 metadata filter를 건다.

```python
query_arguments["where"] = {"run_id": run_id}
```

즉 `run_id=3`이면 vector DB 전체가 아니라 metadata에 `run_id`가 3으로 저장된 chunk만 검색한다.

마지막 줄:

```python
return self.collection.query(**query_arguments)
```

이 줄이 실제 Chroma vector DB 검색이다.

현재 구현에서 vector DB는 이미 저장된 chunk를 대상으로 검색한다. chunk 저장은 `/rag/ask` 흐름이 아니라 인덱싱 흐름에서 미리 이루어진다.

## 7. Embedding Service가 질문을 숫자 벡터로 바꾼다

파일:

```text
backend/app/rag/external/embedding.py
```

관련 코드:

```python
class OpenAIEmbeddingService:
    def __init__(self, model: str = OPENAI_EMBEDDING_MODEL) -> None:
        self.embedding_model = OpenAIEmbeddings(model=model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embedding_model.embed_documents(texts)

    def embed_text(self, text: str) -> list[float]:
        return self.embedding_model.embed_query(text)
```

vector DB는 문자열 자체를 비교하지 않는다. 질문 문자열을 숫자 배열로 바꾼 뒤, 저장된 chunk vector들과 가까운 것을 찾는다.

`embed_text()`는 질문 하나를 검색용 vector로 바꾼다.

```text
"RAG 흐름 설명해줘"
-> [0.012, -0.033, 0.144, ...]
```

인덱싱 시점에는 `embed_texts()`가 여러 chunk 텍스트를 저장용 vector로 바꾼다.

ask 시점에는 `embed_text()`가 사용자 질문을 검색용 vector로 바꾼다.

## 8. Vector 검색 결과를 Row 구조로 바꾼다

파일:

```text
backend/app/rag/domain/vector_result.py
```

관련 코드:

```python
@dataclass(frozen=True)
class VectorResultRow:
    """Chroma가 별도 배열로 주는 검색 결과를 한 행 단위로 묶은 값 객체."""

    id: str
    document: str
    metadata: dict[str, Any]
    distance: float | None
```

Chroma의 검색 결과는 사람이 바로 쓰기 좋은 row 형태가 아니다. 보통 이런 식으로 같은 index끼리 맞춰야 하는 여러 배열 형태다.

```text
ids
documents
metadatas
distances
```

그래서 `parse_vector_result()`가 이 배열들을 같은 index 기준으로 묶는다.

```python
def parse_vector_result(result: dict[str, Any]) -> list[VectorResultRow]:
    """ids, documents, metadata, distance 배열을 같은 index 기준의 row 목록으로 변환한다."""

    ids = get_first_result_list(result, "ids")
    documents = get_first_result_list(result, "documents")
    metadatas = get_first_result_list(result, "metadatas")
    distances = get_first_result_list(result, "distances")

    return [
        VectorResultRow(
            id=chunk_id,
            document=get_list_value(documents, index, ""),
            metadata=get_list_value(metadatas, index, {}) or {},
            distance=get_list_value(distances, index, None),
        )
        for index, chunk_id in enumerate(ids)
    ]
```

이 변환 후에는 answer service가 검색 결과를 다루기 쉬워진다.

```text
VectorResultRow
  id
  document
  metadata
  distance
```

`document`는 LLM에게 줄 근거 텍스트다.

`metadata`에는 citation, path, chunk_type, run_id 같은 추적 정보가 들어 있다.

`distance`는 질문과 chunk 사이의 거리다. 값의 해석은 vector DB 설정에 따라 다르지만, 일반적으로 검색 유사도 판단에 사용된다.

목표 사이클의 `검색 결과 결합`은 현재 코드에서는 아직 복잡하게 구현되어 있지 않다. 현재는 vector 검색 결과를 row로 정리해서 그대로 사용한다.

나중에 SQL 검색과 함께 섞으려면 이 `VectorResultRow` 같은 구조가 결과 결합의 출발점이 될 수 있다.

## 9. 검색 결과가 없으면 기본 답변을 반환한다

파일:

```text
backend/app/rag/service/answer_service.py
```

관련 코드:

```python
if not rows:
    return RagAskResponseDTO(
        answer=NO_EVIDENCE_ANSWER,
        run_id=request.run_id,
        sources=[],
    )
```

검색 결과가 없으면 LLM을 호출하지 않는다.

왜냐하면 이 RAG 서비스의 원칙은 저장된 근거만 사용해 답변하는 것이기 때문이다. 근거가 없는데 LLM을 호출하면 모델이 일반 지식으로 추측할 수 있다.

그래서 현재 코드는 근거가 없을 때 명확히 말한다.

```text
저장된 RAG 근거를 찾지 못했습니다. 먼저 레포지토리 분석을 실행해 주세요.
```

이것은 목표 사이클의 `LLM에게 질문 + 근거 전달` 이전에 있는 방어 로직이다.

## 10. LLM에게 질문과 근거를 전달한다

파일:

```text
backend/app/rag/service/answer_service.py
backend/app/rag/external/llm_client.py
```

answer service는 검색 결과가 있으면 LLM client를 호출한다.

```python
return RagAskResponseDTO(
    answer=self.llm_client.answer_with_evidence(
        question=request.question,
        documents=[row.document for row in rows],
        metadatas=[row.metadata for row in rows],
    ),
    run_id=request.run_id,
    sources=build_sources(rows),
)
```

여기서 LLM으로 넘어가는 값은 세 가지다.

```text
question
  사용자의 원래 질문

documents
  vector 검색으로 찾은 chunk 텍스트들

metadatas
  각 chunk의 citation, path, chunk_type 같은 정보
```

LLM client 쪽에서는 먼저 `RagLlm.answer_with_evidence()`가 호출된다.

```python
class RagLlm:
    def answer_with_evidence(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> str:
        """질문과 근거 목록을 메시지로 바꾼 뒤 선택된 text generator에 위임한다."""

        messages = self.prompt_builder.build_messages(
            question=question,
            documents=documents,
            metadatas=metadatas,
        )
        return self.text_generator.generate(messages)
```

여기서 중요한 분리는 두 가지다.

```text
PromptBuilder
  질문과 근거를 LLM 메시지 구조로 만든다.

TextGenerator
  만들어진 메시지를 실제 모델에 보내고 텍스트 답변을 받는다.
```

이 구조 덕분에 나중에 프롬프트 형식을 바꾸거나 LLM provider를 바꿔도 전체 answer service를 크게 바꾸지 않아도 된다.

## 11. PromptBuilder가 System/User 메시지를 만든다

파일:

```text
backend/app/rag/external/llm_client.py
```

관련 코드:

```python
class PromptBuilder:
    """LLM이 레포 근거만 사용하도록 system/user 메시지 구조를 만든다."""

    def build_messages(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> list[dict[str, str]]:
        """모델 교체와 무관하게 유지할 Chat/Responses API 입력 메시지를 만든다."""

        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self.build_user_prompt(question, documents, metadatas),
            },
        ]
```

`system` 메시지는 모델의 행동 규칙이다.

현재 기본 system prompt는 이런 역할을 한다.

```text
한국어로 답하라.
제공된 repository evidence만 사용하라.
근거가 부족하면 무엇이 부족한지 말하라.
실용적으로 답하고, 필요하면 citation을 포함하라.
```

`user` 메시지는 실제 질문과 검색 근거를 합친 내용이다.

```python
def build_user_prompt(
    self,
    question: str,
    documents: list[str],
    metadatas: list[dict],
) -> str:
    """질문과 citation이 붙은 evidence block을 하나의 사용자 프롬프트로 합친다."""

    evidence = self.evidence_formatter.format(documents, metadatas)
    return f"Question:\n{question.strip()}\n\nEvidence:\n{evidence}"
```

이 단계가 목표 사이클의 이 부분이다.

```text
LLM에게 질문 + 근거 전달
```

## 12. EvidenceFormatter가 근거 블록을 만든다

파일:

```text
backend/app/rag/external/llm_client.py
```

관련 코드:

```python
class EvidenceFormatter:
    """검색된 청크와 metadata를 LLM이 인용 가능한 근거 목록 텍스트로 바꾼다."""

    def format(self, documents: list[str], metadatas: list[dict]) -> str:
        """여러 근거 청크를 번호가 붙은 block으로 이어 붙인다."""

        blocks = [
            self.format_one(index, document, metadatas)
            for index, document in enumerate(documents, start=1)
        ]
        return "\n\n".join(blocks)
```

각 chunk는 citation과 함께 하나의 근거 block으로 바뀐다.

```python
def format_one(
    self,
    index: int,
    document: str,
    metadatas: list[dict],
) -> str:
    """청크 하나에 citation을 붙여 답변 근거로 추적 가능하게 만든다."""

    metadata = get_list_value(metadatas, index - 1, {}) or {}
    citation = metadata.get("citation", UNKNOWN_CITATION)
    return f"[{index}] citation={citation}\n{document.strip()}"
```

결과적으로 LLM에게 들어가는 Evidence는 이런 모양에 가까워진다.

```text
[1] citation=backend/app/rag/service/answer_service.py:26-49
...chunk text...

[2] citation=backend/app/rag/external/vector_repository.py:69-81
...chunk text...
```

이 구조는 모델이 답변할 때 어떤 파일/라인을 근거로 삼았는지 추적할 수 있게 해준다.

## 13. TextGenerator가 실제 LLM을 호출한다

파일:

```text
backend/app/rag/external/llm_client.py
```

관련 코드:

```python
class OpenAIGenerator:
    """OpenAI Responses API 호출을 감싸 다른 LLM provider로 교체하기 쉽게 한다."""

    def __init__(self, model: str = DEFAULT_LLM_MODEL) -> None:
        self.model = model
        self.client = OpenAI()

    def generate(self, messages: list[dict[str, Any]]) -> str:
        """조립된 메시지를 모델에 보내고 화면에 표시할 텍스트만 반환한다."""

        response = self.client.responses.create(
            model=self.model,
            input=messages,
        )
        return response.output_text.strip()
```

이 단계에서 실제 OpenAI API 호출이 일어난다.

입력은 PromptBuilder가 만든 `messages`다.

출력은 화면에 표시할 최종 텍스트다.

현재 구현은 LLM 결과를 복잡하게 JSON으로 파싱하지 않고, `response.output_text.strip()`으로 텍스트 답변만 꺼낸다.

목표 사이클의 `LLM 결과 해석`은 현재 구현에서는 아주 단순하다.

```text
LLM 결과 해석
-> output_text를 문자열 답변으로 사용
```

나중에 agent workflow로 확장하면 이 부분에서 결과를 구조화할 수 있다.

예:

```text
answer
action_required
action_type
action_payload
confidence
```

## 14. 응답 DTO로 포장한다

파일:

```text
backend/app/rag/service/answer_service.py
backend/app/rag/api/schema.py
```

LLM 답변을 받은 뒤 `RagAnswerService.answer()`는 최종 응답 DTO를 만든다.

```python
return RagAskResponseDTO(
    answer=self.llm_client.answer_with_evidence(
        question=request.question,
        documents=[row.document for row in rows],
        metadatas=[row.metadata for row in rows],
    ),
    run_id=request.run_id,
    sources=build_sources(rows),
)
```

응답 DTO 구조는 이렇다.

```python
class RagAskResponseDTO(BaseModel):
    answer: str
    run_id: int | None = None
    sources: list[RagAskSourceDTO]
```

`answer`는 LLM이 만든 최종 답변이다.

`run_id`는 어떤 인덱싱 실행 범위를 기준으로 답했는지 표시한다.

`sources`는 답변 아래에 보여줄 출처 목록이다.

출처 목록은 `build_sources()`에서 만든다.

```python
def build_sources(rows: list[VectorResultRow]) -> list[RagAskSourceDTO]:
    """LLM 답변 아래에 노출할 citation, path, 거리 정보를 검색 결과에서 추출한다."""

    sources: list[RagAskSourceDTO] = []
    for row in rows:
        sources.append(
            RagAskSourceDTO(
                citation=str(row.metadata.get("citation", "")),
                path=str(row.metadata.get("path", "")),
                chunk_type=str(row.metadata.get("chunk_type", "")),
                distance=row.distance,
            )
        )
    return sources
```

`sources`는 사용자가 답변의 근거를 확인할 수 있게 해준다.

예:

```json
{
  "answer": "이 레포의 RAG ask 흐름은 ...",
  "run_id": 3,
  "sources": [
    {
      "citation": "backend/app/rag/service/answer_service.py:26-49",
      "path": "backend/app/rag/service/answer_service.py",
      "chunk_type": "function",
      "distance": 0.22
    }
  ]
}
```

## 15. 라우터가 클라이언트에게 응답한다

다시 파일:

```text
backend/app/rag/api/router.py
```

`ask_repository_rag()`는 `answer_service.answer(request)`의 결과를 그대로 반환한다.

```python
return answer_service.answer(request)
```

FastAPI는 이 반환값을 `response_model=RagAskResponseDTO`에 맞춰 JSON으로 직렬화한다.

즉 전체 흐름은 이렇게 끝난다.

```text
RagAnswerService.answer()
-> RagAskResponseDTO
-> FastAPI JSON response
-> Client
```

## 목표 사이클과 현재 코드 매핑

아래 표는 처음에 세운 사고 사이클을 현재 코드에 매핑한 것이다.

| 목표 사이클 | 현재 코드 | 상태 |
| --- | --- | --- |
| 사용자 입력 | `POST /rag/ask` | 구현됨 |
| 입력을 요청 DTO로 받기 | `RagAskRequestDTO` | 구현됨 |
| 어떤 작업인지 판단 | `/rag/ask`로 들어오면 RAG 답변으로 고정 | 구조만 있음 |
| 검색 계획 세우기 | `RagAnswerService.answer()`에서 vector search만 선택 | 구조만 있음 |
| SQL 검색 / Vector 검색 | `RagVectorRepository.search()` | Vector는 구현됨, SQL은 ask 흐름에 미연결 |
| 검색 결과 결합 | `parse_vector_result()`로 row 정리 | 구조만 있음 |
| LLM에게 질문 + 근거 전달 | `RagLlm.answer_with_evidence()` | 구현됨 |
| LLM 결과 해석 | `OpenAIGenerator.generate()`가 텍스트 반환 | 단순 구현 |
| 사용자에게 답변하거나, 다음 로직 실행 | `RagAskResponseDTO` 반환 | 사용자 응답만 구현 |

## 구조만 있는 흐름을 실제 코드에 끼우면

아래는 아직 완전히 구현된 흐름이 아니라, 현재 구조 위에 자연스럽게 추가할 수 있는 설계 흐름이다. 각 항목은 `구조만 있음`으로 표시한다.

### 1. Intent 판단

상태: 구조만 있음

현재 `/rag/ask`는 모든 입력을 답변 생성 요청으로 본다.

추가된다면 위치는 `ask_repository_rag()`와 `RagAnswerService.answer()` 사이가 자연스럽다.

```text
ask_repository_rag()
-> AgentOrPlannerService.plan(request.question)
-> plan.type에 따라 분기
```

예상 역할:

```text
사용자 질문인지
코드 위치 검색인지
GitHub issue 생성 요청인지
보드 작업 생성 요청인지
추가 인덱싱 요청인지 판단
```

현재 코드에서는 `AnswerUseCase`라는 포트 타입으로 answer service를 주입받는다. 이처럼 인터페이스를 사이에 두는 구조는 나중에 `PlannerUseCase`나 `AgentUseCase`를 끼우기 좋다.

### 2. 검색 계획 세우기

상태: 구조만 있음

현재 `RagAnswerService.answer()`는 바로 vector 검색을 실행한다.

```python
search_result = self.vector_repository.search(
    query=request.question,
    limit=request.limit,
    run_id=request.run_id,
)
```

나중에 검색 계획이 들어가면 이런 구조가 될 수 있다.

```text
question
-> RetrievalPlan
   - use_vector: true
   - use_sql: true
   - keyword: ...
   - run_id: ...
   - limit: ...
```

예상 위치:

```text
RagAnswerService.answer()
-> RetrievalPlanner.build_plan(request)
-> retrievers 실행
```

### 3. SQL 검색

상태: 일부 구현됨, ask 흐름에는 미연결

SQL 저장소는 이미 RAG 인덱스 실행 결과와 chunk를 저장/조회하는 책임을 가진다.

현재 ask 흐름은 `RagSqlRepository`를 사용하지 않는다. 하지만 keyword 기반 검색이나 run 상세 조회 같은 구조는 이미 SQL repository 쪽에 있다.

추가된다면 흐름은 이렇게 될 수 있다.

```text
RagAnswerService.answer()
-> sql_retriever.search(keyword, run_id, limit)
-> vector_retriever.search(question, run_id, limit)
```

SQL 검색이 유리한 경우:

```text
정확한 함수명 검색
정확한 파일 경로 검색
특정 chunk_type 검색
특정 run_id 안의 chunk 확인
```

### 4. SQL / Vector 결과 결합

상태: 구조만 있음

현재는 `parse_vector_result()`로 vector 검색 결과만 `VectorResultRow` 목록으로 만든다.

```text
Chroma result dict
-> list[VectorResultRow]
```

나중에 SQL 결과까지 섞으려면 공통 결과 타입이 필요하다.

예상 구조:

```text
VectorResultRow
SqlResultRow
-> EvidenceCandidate
-> 중복 제거
-> 점수 계산
-> 상위 N개 선택
```

이 단계가 들어가면 LLM은 SQL 결과와 vector 결과가 합쳐진 evidence만 받게 된다.

### 5. LLM 결과 구조화

상태: 구조만 있음

현재 LLM 응답은 단순 문자열이다.

```python
return response.output_text.strip()
```

나중에 agent workflow로 가려면 LLM 결과를 구조화해야 한다.

예상 응답:

```json
{
  "type": "answer",
  "answer": "...",
  "sources": []
}
```

또는:

```json
{
  "type": "action",
  "action": "create_github_issue",
  "payload": {
    "title": "...",
    "body": "..."
  }
}
```

이 구조가 생기면 `LLM 결과 해석` 단계가 단순 텍스트 반환에서 `결과 타입 판별`로 바뀐다.

### 6. 다음 로직 실행

상태: 구조만 있음

현재 `/rag/ask`는 항상 사용자에게 답변을 반환한다.

```text
RagAskResponseDTO
-> Client
```

나중에 action 실행이 들어가면 아래처럼 갈라진다.

```text
LLM result type == answer
-> 사용자에게 답변

LLM result type == action
-> ActionExecutor 실행
-> GitHub / Board / DB 작업
-> 실행 결과를 사용자에게 반환
```

이 단계는 MCP나 agent와 연결될 수 있다. 예를 들어 LLM이 `create_issue` action을 선택하면, GitHub 관련 도구나 service를 호출하는 식이다.

## 현재 구현의 핵심 흐름

현재 `/rag/ask`를 한 줄로 말하면 아래와 같다.

```text
질문을 받는다.
질문을 embedding한다.
vector DB에서 비슷한 chunk를 찾는다.
찾은 chunk를 citation과 함께 LLM에게 준다.
LLM 답변과 source 목록을 사용자에게 돌려준다.
```

코드 흐름은 아래처럼 기억하면 된다.

```text
ask_repository_rag(request)
-> answer_service.answer(request)
-> vector_repository.search(request.question, request.limit, request.run_id)
-> embedding_service.embed_text(question)
-> Chroma collection.query(...)
-> parse_vector_result(...)
-> llm_client.answer_with_evidence(question, documents, metadatas)
-> PromptBuilder + EvidenceFormatter
-> OpenAIGenerator.generate(messages)
-> RagAskResponseDTO(answer, run_id, sources)
```

## 앞으로 확장할 수 있는 지점

네가 말한 완성형 사이클에는 아직 현재 코드에 없는 단계들이 있다.

### 1. 어떤 작업인지 판단

현재는 `/rag/ask`로 들어오면 무조건 답변 생성이다.

나중에는 사용자의 프롬프트를 보고 아래처럼 나눌 수 있다.

```text
질문 답변
코드 위치 찾기
보드 작업 생성
GitHub issue 생성
PR comment 작성
추가 인덱싱 요청
```

이 단계가 생기면 `IntentDetector`, `Planner`, `AgentService` 같은 객체가 들어올 수 있다.

### 2. SQL 검색 추가

현재 `/rag/ask`는 vector 검색만 한다.

하지만 SQL에는 chunk 원문, 경로, run 기록, skipped file 등이 구조적으로 저장되어 있다.

추가할 수 있는 검색:

```text
keyword 기반 chunk_text ilike 검색
path 기반 검색
chunk_type 기반 검색
run_id 기반 상세 검색
```

이것은 `RagSqlRepository`나 별도의 `SqlRetriever`로 분리할 수 있다.

### 3. SQL / Vector 결과 결합

Vector 검색은 의미적으로 비슷한 chunk를 찾는 데 좋다.

SQL 검색은 정확한 키워드, 경로, 타입 조건에 강하다.

둘을 합치려면 중간에 result fusion 단계가 필요하다.

```text
VectorResultRow
SqlResultRow
-> 공통 EvidenceCandidate
-> 중복 제거
-> 점수 계산
-> 상위 N개 선택
```

현재 `VectorResultRow`는 그 확장의 출발점이 될 수 있다.

### 4. LLM 결과 해석

현재 LLM 결과는 단순 텍스트다.

agent로 확장하려면 LLM이 구조화된 결과를 반환하게 할 수 있다.

```json
{
  "type": "answer",
  "answer": "...",
  "needs_action": false,
  "sources": []
}
```

또는:

```json
{
  "type": "action",
  "action": "create_issue",
  "payload": {
    "title": "...",
    "body": "..."
  }
}
```

### 5. 사용자에게 답변하거나 다음 로직 실행

현재는 항상 사용자에게 `RagAskResponseDTO`를 반환한다.

나중에는 아래처럼 갈라질 수 있다.

```text
LLM 결과가 최종 답변이면
  -> 사용자에게 반환

LLM 결과가 action 요청이면
  -> action executor 실행
  -> 실행 결과를 사용자에게 반환
```

이 지점부터는 단순 RAG가 아니라 agent workflow가 된다.

## 요약

현재 `/rag/ask`는 완성형 agent 사이클의 첫 버전이다.

구현된 흐름:

```text
사용자 질문
-> DTO 검증
-> 인증 확인
-> vector 검색
-> 검색 결과 row 변환
-> LLM에게 질문 + 근거 전달
-> 답변 + 출처 반환
```

아직 확장 전인 흐름:

```text
의도 판단
SQL 검색
SQL/Vector 결과 결합
LLM 결과 구조화
후속 action 실행
```

따라서 공부할 때는 먼저 현재 구현된 `/rag/ask` 흐름을 손으로 따라가고, 그 다음에 SQL 검색과 agent action을 어디에 끼울지 생각하면 된다.
