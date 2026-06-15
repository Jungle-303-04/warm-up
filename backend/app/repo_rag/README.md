# repo_rag 모듈 가이드

GitHub 저장소를 동기화해 심볼 단위로 청킹·임베딩하고, Postgres(pgvector)에 저장한 뒤
키워드+벡터 하이브리드 검색을 제공하는 모듈. 헥사고날(포트/어댑터) + 레이어드 구조.

## 계층과 의존성 방향

```
api/            router · schemas(DTO)              ← HTTP 입력 어댑터
  │ Depends
application/    service · worker · indexing ·       ← 유스케이스(트랜잭션 경계 = with uow)
                producer · cleanup · search_service ·
                unit_of_work · types
  │ 포트에만 의존
domain/         ports(EmbeddingClient·RepoRagStore· ← 순수 규칙(외부 의존 없음)
                RepoRagRetriever) · chunking ·
                python_classifier · chunk_identity ·
                text_splitter · diff · records · retrieval · identity
  ▲ 구현
infrastructure/ in_memory_store · sql_store ·        ← 어댑터(기술 결합)
                sql_retriever · sql_unit_of_work ·
                db · models · mappers · embeddings
repository_source/   repo_sync(git clone)
config.py  ·  dependencies.py(FastAPI 조립 지점)  ·  poller.py(백그라운드 워커)
```

규칙: **안쪽(domain/application)은 바깥(infrastructure)을 import 하지 않는다.** 구현 선택은
`dependencies.py`가 환경변수(`POSTGRES_DATABASE_URL`)로 결정한다.

## "어디에 추가하나" 빠른 안내

- **새 언어 청커**: `domain/chunking.py`에 `LanguageChunker` 구현 → `DEFAULT_CHUNKER_REGISTRY`에 등록.
- **새 임베딩 제공자**: `infrastructure/embeddings.py`에 `EmbeddingClient` 구현 → `dependencies.build_embedding_client`에 분기.
- **새 저장소 백엔드**: `RepoRagStore` 포트(`domain/ports.py`) 구현 + 그에 맞는 `UnitOfWork` →
  `dependencies.get_uow_factory`에 분기.
- **새 엔드포인트**: `api/router.py` + `api/schemas.py`. 트랜잭션이 필요하면 `with uow_factory() as uow:`.

## 트랜잭션 경계 (핵심)

서비스가 `with self.uow_factory() as uow:`로 경계를 잡고, 그 안의 모든 저장소 호출이
하나의 세션/트랜잭션을 공유한다. 정상 종료 시 commit, 예외 시 rollback.
- HTTP: `dependencies.get_uow_factory`가 in-memory/SQL UoW를 주입.
- 백그라운드 워커: `poller.py`가 같은 서비스를 재사용(`service.process`).

## 동작 흐름

- **sync** (`POST /pipeline/sync`): in-memory면 인라인 실행(200), Postgres면 큐잉 후 202 +
  워커(`python -m app.repo_rag.poller`)가 처리. 상태는 `GET /pipeline/sync/{job_id}`.
- **search** (`POST /pipeline/search`, Postgres 전용): 저장소 resolve → 벡터(코사인) +
  키워드(ts_rank_cd) 후보를 `domain/retrieval.fuse_scores`로 가중합.

실행 절차는 `backend/docs/repo-rag.md`, 로드맵은 `docs/woonyong/repo-rag-roadmap.md` 참고.
