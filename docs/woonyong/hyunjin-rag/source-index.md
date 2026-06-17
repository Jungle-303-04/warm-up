# HYUNJIN 브랜치 RAG 자료 색인

분석 대상은 `Jungle-12-303/week15-16_team03_ai_board_lab` 저장소의 `HYUNJIN` 브랜치만으로 제한한다.

- 기준 커밋: `ca56e75e115987b095e4806cf81f234a1d371465`
- 원격 브랜치: `https://github.com/Jungle-12-303/week15-16_team03_ai_board_lab/tree/HYUNJIN`
- 작성 목적: RepoLM의 RAG 검색, 답변 grounding, 평가 체계를 보강하기 위한 참고 자료를 한곳에 정리한다.

## 핵심 문서

| 경로 | 역할 | RepoLM에 주는 시사점 |
| --- | --- | --- |
| `docs/rag-performance-report.md` | 최종 RAG 성능 리포트 | 평가 지표를 `MRR@5`, `Hit@5`, `NDCG@5`, `Precision@5`, `Recall@5`로 나누고 실제 API 경로 기준으로 채택 여부를 결정한다. |
| `docs/rag-measurement-inventory.md` | 실험 결과 인벤토리 | 서로 다른 평가셋을 한 리더보드로 섞지 않고, offline/online/scenario/RAGAS를 분리해서 해석한다. |
| `docs/rag-scenario-evaluation.md` | 실제 입출력 시나리오 평가 | 정량 지표로 잡히지 않는 UX 실패를 케이스별로 기록한다. |
| `docs/textbook/04-rag.md` | RAG 구조 교재 | chunking, embedding queue, hybrid retrieval, fallback generation을 설명한다. |
| `docs/textbook/06-operations-evaluation.md` | 운영/평가 교재 | 검색 평가는 retrieval script, 생성 평가는 RAGAS로 분리한다. |
| `eval/ragas/README.md` | RAGAS 실행 가이드 | faithfulness, answer relevancy, context precision/recall을 생성 품질 보조 지표로 사용한다. |

## 핵심 구현

| 경로 | 역할 | 관찰한 설계 |
| --- | --- | --- |
| `SimilarPostSearchService.java` | 최종 검색 랭킹 | Qdrant 후보, BM25, RRF, keyword/guard term, metadata relaxation, chunk evidence를 결합한다. |
| `RagDraftService.java` | RAG 초안 생성 | 강한 근거만 prompt source로 넣고, 근거가 약하면 fallback을 반환한다. |
| `PostChunkTextSplitter.java` | 게시글 chunking | 문단 보존을 우선하고 긴 문단은 길이 기준으로 나눈다. |
| `RagSearchProperties.java` | 검색 파라미터 | BM25, RRF, query mode, chunk evidence, metadata 사용 여부를 설정값으로 관리한다. |
| `EmbeddingJobService/Scheduler/Processor.java` | 임베딩 작업 큐 | 저장 후 비동기로 임베딩하고 재시도/실패 상태를 남긴다. |
| `QdrantVectorStoreClient.java` | 벡터 DB 연동 | Qdrant를 1차 후보 검색기로 사용한다. |

## 평가 스크립트

| 경로 | 역할 | RepoLM 적용 방향 |
| --- | --- | --- |
| `scripts/evaluate-rag-retrieval.mjs` | 고정 케이스 기반 retrieval 평가 | RepoLM도 질문별 기대 file path/chunk id를 둔 golden set이 필요하다. |
| `scripts/evaluate-rag-online-candidates.mjs` | 실제 서버를 후보 설정별로 띄워 API 평가 | RepoLM도 top_k, vector/keyword weight, RRF, context expansion, trust policy를 후보군으로 비교해야 한다. |
| `scripts/evaluate-rag-offline-ablation.mjs` | offline ablation | 빠른 후보 축소용으로 쓰되 최종 채택은 online 결과를 따라야 한다. |
| `scripts/evaluate-chunk-size-variants.mjs` | chunk 크기 실험 | Markdown/PDF/code/text별 chunk 정책도 실험값으로 비교해야 한다. |
| `scripts/evaluate-rag-scenarios.mjs` | 시나리오 평가 | 모호한 질문, 충돌, 근거 없음, 다이어그램 생성 흐름을 사용자 관점에서 검증해야 한다. |

## 최종 채택 지표

HYUNJIN 브랜치의 최종 online 후보 검증은 `Combined tuned` 조합을 채택한다.

| 지표 | 값 |
| --- | ---: |
| `Precision@5` | `0.8667` |
| `Recall@5` | `0.4957` |
| `MRR@5` | `1.0000` |
| `NDCG@5` | `0.9076` |
| `Hit@5` | `1.0000` |

최종 조합의 핵심 설정은 `TITLE_CONTENT` query, Qdrant 후보 검색, BM25/RRF 재정렬, query/guard term `12/6`, chunk evidence `0.03`, metadata enabled다.

## 해석 원칙

- offline 평가는 빠르게 후보를 줄이기 위한 도구다.
- 최종 채택은 실제 Spring Boot 서버와 Qdrant/MySQL/OpenAI 경로를 모두 타는 online 평가를 따른다.
- RAGAS는 생성 답변의 grounded 품질을 보는 보조 평가이며 retrieval ranking 지표를 대체하지 않는다.
- 같은 `top5`라도 첫 관련 결과가 어디에 나오는지가 중요하므로 작성 보조 UX에서는 `MRR@5`, `Hit@5`, `NDCG@5`를 `Recall@5`보다 우선한다.
- 관련 글 전체를 모두 찾는 기능이 아니라 상위 추천 품질이 중요한 기능에서는 낮은 `Recall@5`를 단독 실패로 보지 않는다.
