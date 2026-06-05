# 02. RAG

참고:

- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [LangGraph Agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [pgvector](https://github.com/pgvector/pgvector)

RAG는 LLM이 우리 데이터에 근거해서 답하게 만드는 구조다.  
핵심은 "검색 결과를 prompt에 넣는다"가 아니라, 어떤 데이터를 어떤 단위로 저장하고 어떤 기준으로 다시 찾을지 설계하는 것이다.

## RAG가 필요한 질문

RAG는 아래 질문에 강하다.

```text
"우리 게시판에 FastAPI 인증 관련 글 있어?"
"지난주 회의록에서 결정된 DB가 뭐였지?"
"이 에러랑 비슷한 사례가 있었어?"
"이 문서 내용을 바탕으로 요약해줘"
"내가 쓰는 글과 중복되는 기존 글을 찾아줘"
```

반대로 아래처럼 일반 지식이나 창작에 가까운 요청은 RAG 없이도 가능하다.

```text
"REST가 뭐야?"
"자기소개 문장을 더 자연스럽게 바꿔줘"
"React 컴포넌트 이름 추천해줘"
```

서비스 관점에서는 먼저 intent를 나눈다.

```text
RAG 필요
- 내부 데이터, 최신 데이터, 특정 문서, 근거 링크가 필요함

RAG 불필요
- 일반 설명, 문장 다듬기, 간단한 생성

애매함
- 사용자에게 범위를 물어보거나, 가벼운 검색을 먼저 해봄
```

## Ingestion Pipeline

RAG는 답변할 때보다 데이터를 넣을 때가 더 중요하다.  
검색할 데이터가 잘못 들어가면 LLM은 아무리 좋아도 틀린 근거를 보고 답한다.

```text
source 수집
-> parser
-> cleaning
-> chunking
-> metadata 부여
-> embedding
-> vector DB 저장
-> 색인 상태 기록
```

### Source

데이터 원천은 여러 종류가 될 수 있다.

```text
게시글
- title, content, author, tags, created_at

댓글
- content, post_id, author, created_at

문서
- markdown, PDF, txt, docx

외부 데이터
- GitHub README, issue, PR, API 결과

운영 지식
- FAQ, 공지, 회고, 결정 기록
```

source마다 metadata가 중요하다.  
검색 결과가 나왔을 때 "어디에서 온 정보인지"를 보여줘야 citation이 가능하다.

### Parser

Parser는 원본 데이터를 검색 가능한 text로 바꾼다.

```text
Markdown
- heading, code block, paragraph 구조 유지

HTML
- script/style 제거
- 본문 텍스트 추출

PDF
- 페이지 번호 유지
- 표/이미지 설명은 별도 처리

게시글
- 제목과 본문을 분리해서 metadata로 보존
```

PDF는 특히 조심해야 한다. 텍스트 추출이 깨질 수 있고, 표나 이미지 안의 의미가 사라질 수 있다.  
중요 문서는 추출 결과를 사람이 확인하는 디버그 화면이 있으면 좋다.

### Cleaning

검색 품질을 떨어뜨리는 노이즈를 줄인다.

```text
제거할 수 있는 것
- 반복되는 footer
- 광고/메뉴 텍스트
- 너무 긴 공백
- 깨진 문자
- 의미 없는 boilerplate

보존해야 하는 것
- 제목
- 코드 블록
- 에러 메시지
- 표의 핵심 값
- 링크
```

코드나 에러 메시지는 일반 문장처럼 정리하면 안 된다.  
`ModuleNotFoundError`, `401 Unauthorized`, `SQLAlchemy async session` 같은 정확한 문자열은 검색에 중요하다.

## Chunking

Chunking은 긴 문서를 검색 단위로 나누는 일이다.  
RAG 품질을 가장 많이 좌우하는 부분 중 하나다.

### 너무 큰 chunk

```text
장점
- 문맥이 유지됨

문제
- 검색 결과가 흐려짐
- 불필요한 내용이 많이 들어감
- token 비용 증가
```

### 너무 작은 chunk

```text
장점
- 특정 문장을 정확히 찾기 쉬움

문제
- 앞뒤 맥락이 사라짐
- 답변할 때 근거가 부족해짐
```

### 추천 시작점

처음에는 아래 정도로 시작한다.

```text
chunk_size: 500-1000 tokens
overlap: 100-200 tokens
split 기준: heading -> paragraph -> sentence
```

게시글처럼 짧은 데이터는 글 하나를 chunk로 둬도 된다.  
긴 문서나 PDF는 heading 단위와 token 단위를 섞어서 나누는 것이 좋다.

### Chunk metadata

각 chunk에는 반드시 출처 정보를 붙인다.

```json
{
  "source_type": "post",
  "source_id": "post_123",
  "chunk_index": 2,
  "title": "FastAPI JWT 인증 오류 정리",
  "author_id": "user_7",
  "tags": ["fastapi", "auth", "jwt"],
  "created_at": "2026-06-06T10:00:00+09:00",
  "url": "/posts/123"
}
```

metadata가 없으면 검색 결과를 답변에 넣을 수는 있어도, 사용자에게 근거를 보여주기 어렵다.

## Embedding

Embedding은 텍스트를 벡터로 바꾸는 과정이다.  
OpenAI embeddings 문서에서도 embeddings는 검색, 클러스터링, 추천, 분류 등에 사용되는 관련도 표현이라고 설명한다.

RAG에서는 두 종류의 텍스트를 같은 embedding model로 벡터화한다.

```text
문서 chunk -> embedding 저장
사용자 질문 -> embedding 생성 후 검색
```

서로 다른 embedding model을 섞으면 유사도 비교가 깨진다.  
따라서 embedding model, dimension, 전처리 방식을 저장해둬야 한다.

```text
embedding_model
embedding_dimension
content_hash
embedded_at
```

content_hash를 저장하면 같은 내용의 chunk를 다시 embedding하지 않아도 된다.

## Vector Store

PostgreSQL을 메인 DB로 쓴다면 pgvector가 자연스럽다.  
게시글, 댓글, 사용자, 태그 같은 관계형 데이터와 vector를 한 DB 안에서 다룰 수 있기 때문이다.

예시 테이블 구조:

```sql
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT,
    url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES rag_documents(id),
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

dimension은 사용하는 embedding model에 맞춰 정해야 한다.

## Retrieval

검색은 단순히 vector similarity top-k만 뽑는 것으로 끝나지 않는다.

```text
query 생성
-> metadata filter 적용
-> vector search
-> keyword search 선택적 병합
-> rerank
-> context packing
```

### Vector Search

의미가 비슷한 문서를 찾는 데 좋다.

```text
"로그인이 안돼"
-> "JWT 토큰 만료", "401 Unauthorized", "인증 미들웨어" 문서가 잡힐 수 있음
```

### Keyword Search

정확한 문자열이 중요한 경우에 좋다.

```text
ModuleNotFoundError
SQLSTATE 23505
OAuth2
pgvector
```

### Hybrid Search

실제 서비스에서는 vector와 keyword를 섞는 쪽이 안정적이다.

```text
semantic_score = vector similarity
keyword_score = text search rank
final_score = semantic_score * 0.7 + keyword_score * 0.3
```

정확한 공식은 프로젝트에 맞게 조정한다. 중요한 건 검색 결과를 눈으로 보고 조정할 수 있어야 한다는 점이다.

## Context Packing

검색된 chunk를 그대로 다 넣으면 안 된다.  
LLM prompt에는 제한된 context budget이 있고, 중복된 정보가 많으면 답변 품질이 떨어진다.

ContextBuilder는 아래 일을 한다.

```text
중복 chunk 제거
점수 낮은 chunk 제외
출처별 균형 조정
긴 chunk 요약 또는 절단
답변에 필요한 citation id 부여
```

예시:

```text
[source: post_123, chunk: 2, score: 0.87]
FastAPI에서 JWT 인증 실패가 발생하는 가장 흔한 이유는 ...

[source: comment_991, chunk: 0, score: 0.78]
작성자는 Authorization 헤더에 Bearer prefix가 빠져 있었다고 설명했다.
```

## Answer Generation

RAG 답변 프롬프트는 일반 답변 프롬프트와 달라야 한다.

```text
규칙
- 제공된 context 안에서만 답변한다.
- 근거가 부족하면 부족하다고 말한다.
- 추측을 사실처럼 말하지 않는다.
- 답변 끝에 사용한 출처를 표시한다.
- 서로 충돌하는 근거가 있으면 충돌을 밝힌다.
```

RAG 답변에서 가장 위험한 것은 "검색 결과는 맞는데 모델이 그 밖의 내용을 지어내는 것"이다.  
그래서 citation과 answer verification이 중요하다.

## RAG Evaluation

RAG는 반드시 평가해야 한다.  
LLM 답변만 보고 "괜찮아 보인다"로 판단하면 검색 품질 문제를 놓친다.

### Retrieval 평가

```text
Recall@k
- 정답 문서가 top-k 안에 들어왔는가

MRR
- 정답 문서가 얼마나 위에 나왔는가

Hit Rate
- 관련 문서를 하나라도 찾았는가

Filter Accuracy
- 태그/기간/작성자 필터가 제대로 적용됐는가
```

### Answer 평가

```text
Groundedness
- 답변이 검색 근거에 기반하는가

Citation Accuracy
- 인용한 출처가 실제 답변 내용을 뒷받침하는가

Completeness
- 질문에 필요한 내용을 빠뜨리지 않았는가

Abstention
- 근거가 부족할 때 모른다고 말하는가
```

### Golden Set

평가용 질문 세트를 따로 만든다.

```json
{
  "question": "FastAPI JWT 인증 실패 원인은?",
  "expected_sources": ["post_123", "comment_991"],
  "must_include": ["Authorization 헤더", "Bearer", "토큰 만료"],
  "must_not_include": ["OAuth2 설정만의 문제라고 단정"]
}
```

이런 평가 데이터가 있어야 chunking이나 embedding model을 바꿨을 때 좋아졌는지 나빠졌는지 알 수 있다.

## RAG 실패 패턴

```text
검색 결과 없음
- query rewrite 필요
- keyword search 병합 필요
- metadata filter가 너무 강할 수 있음

엉뚱한 문서 검색
- chunk가 너무 큼
- embedding 품질 문제
- metadata 부족

검색은 맞는데 답변이 틀림
- prompt 규칙 부족
- context packing 문제
- answer verification 필요

답변에 출처 없음
- source metadata 설계 부족
- citation format 누락

비용 과다
- top-k가 너무 큼
- 중복 context가 많음
- 긴 tool output까지 같이 넣음
```

## Python 클래스 구조

```python
from typing import Protocol
from pydantic import BaseModel


class RagChunk(BaseModel):
    id: str
    content: str
    score: float
    source_type: str
    source_id: str
    url: str | None = None
    metadata: dict


class VectorStore(Protocol):
    async def upsert_chunks(self, chunks: list[RagChunk]) -> None:
        ...

    async def search(
        self,
        query_embedding: list[float],
        filters: dict,
        limit: int,
    ) -> list[RagChunk]:
        ...


class Retriever(Protocol):
    async def retrieve(self, query: str, filters: dict, limit: int) -> list[RagChunk]:
        ...
```

구현체는 infrastructure에 둔다.

```text
domain/ports.py              -> VectorStore, EmbeddingClient Protocol
application/retrieve.py      -> RetrieveRelevantContextUseCase
infrastructure/pgvector.py   -> PgVectorStore
infrastructure/openai.py     -> OpenAIEmbeddingClient
```

