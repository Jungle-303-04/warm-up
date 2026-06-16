# repo-rag: Postgres + pgvector 하이브리드 검색

GitHub 저장소를 동기화해 심볼/섹션 단위로 청킹하고, OpenAI 임베딩과 함께
Postgres(pgvector)에 저장한 뒤, 키워드(tsvector) + 벡터(pgvector) 하이브리드
검색을 제공한다.

## 구성 요소

- 청킹: `app/repo_rag/domain/chunking.py`
  - Python은 AST 심볼 단위(`python_classifier.py`로 역할 분류), Markdown은 heading 섹션
- 임베딩: `app/repo_rag/domain/ports.py`(포트) + `infrastructure/embeddings.py`
  - `OpenAIEmbeddingClient`(text-embedding-3-small, 1536) / `DeterministicEmbeddingClient`(오프라인)
- 저장소: `infrastructure/store.py`(포트) + `in_memory_store.py` / `sql_store.py`(Postgres)
- 검색: `domain/retrieval.py`(점수 융합) + `infrastructure/sql_retriever.py`
- 모델/스키마: `infrastructure/models.py`, `sql/001_repo_rag_indexes.sql`

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `POSTGRES_DATABASE_URL` | 설정 시 Postgres 저장소 사용, 없으면 in-memory | (없음) |
| `EMBEDDING_PROVIDER` | `openai` 또는 `deterministic` | `deterministic` |
| `EMBEDDING_MODEL` | OpenAI 임베딩 모델 | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | 벡터 차원(모델과 일치해야 함) | `1536` |
| `OPENAI_API_KEY` | OpenAI 키 | (없음) |
| `HYBRID_VECTOR_WEIGHT` | 벡터 가중치 | `0.7` |
| `HYBRID_KEYWORD_WEIGHT` | 키워드 가중치 | `0.3` |
| `SEARCH_TEXT_CONFIG` | Postgres 전문검색 config | `simple` |
| `SEARCH_CANDIDATE_LIMIT` | 각 채널 후보 수 | `50` |

> `EMBEDDING_DIMENSION`을 바꾸면 `source_chunks.embedding` 컬럼 차원도 달라지므로
> 스키마를 다시 만들어야 한다.

## 실행 절차

```bash
# 1) 의존성 동기화
cd backend
uv sync                      # 또는 pip install -e .

# 2) Postgres + pgvector 준비 (예시: docker)
docker run -d --name repolm-pg -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=repolm \
  pgvector/pgvector:pg16

export POSTGRES_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/repolm"
export EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# 3) 스키마 초기화 (확장 + 테이블 + HNSW/GIN 인덱스)
python -m scripts.init_db

# 4) 서버 실행
uvicorn app.main:app --reload

# 4-1) sync 워커 실행 (Postgres 경로 전용, 별도 프로세스)
#      /pipeline/sync는 job을 큐에 넣고 202를 반환하며, 실제 처리는 이 워커가 폴링한다.
POSTGRES_DATABASE_URL=... python -m app.repo_rag.poller

# 5) GitHub 저장소 동기화 (Postgres: 202 + job_id 반환, 워커가 클론→청킹→임베딩→저장)
curl -X POST localhost:8000/pipeline/sync \
  -H 'content-type: application/json' \
  -d '{"repository":"Jungle-303-04/warm-up","branch":"woonyong",
       "repository_url":"https://github.com/Jungle-303-04/warm-up.git"}'

# 5-1) job 상태/이벤트 조회
curl localhost:8000/pipeline/sync/<job_id>

# 6) 하이브리드 검색
curl -X POST localhost:8000/pipeline/search \
  -H 'content-type: application/json' \
  -d '{"query":"login token", "repository":"Jungle-303-04/warm-up",
       "branch":"woonyong",
       "repository_url":"https://github.com/Jungle-303-04/warm-up.git",
       "limit":5}'
```

## 테스트

```bash
# 오프라인(청킹/임베딩/융합/동기화) — DB 불필요
pytest

# Postgres 통합 테스트 (테스트 전용 DB 권장)
POSTGRES_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/repolm_test" \
  pytest tests/repo_rag/test_sql_integration.py
```

## 검색 점수

각 채널 점수를 후보 집합 안에서 [0,1]로 정규화한 뒤 가중합한다.

```
final = HYBRID_VECTOR_WEIGHT * vector_norm + HYBRID_KEYWORD_WEIGHT * keyword_norm
```

- 벡터: pgvector 코사인 거리(`<=>`)의 유사도(`1 - distance`), HNSW 인덱스
- 키워드: `to_tsvector(simple, text)` 생성 컬럼 + `ts_rank_cd`, GIN 인덱스
- active(`is_active`, `deleted_at IS NULL`) 청크만 검색 대상
