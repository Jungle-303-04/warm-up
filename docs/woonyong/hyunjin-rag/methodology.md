# HYUNJIN 브랜치 RAG 방법론 정리

이 문서는 HYUNJIN 브랜치의 RAG 구현과 평가 방식을 RepoLM에 이식 가능한 원칙으로 압축한 것이다. 외부 레포 분석은 `HYUNJIN` 브랜치 기준 커밋 `ca56e75e115987b095e4806cf81f234a1d371465`만 사용했다.

## 1. RAG 파이프라인

HYUNJIN의 RAG는 단일 vector search가 아니라 `원본 저장소 + 벡터 후보 + 키워드 재정렬 + 생성 gate`로 구성된다.

1. 게시글 원문은 MySQL에 저장한다.
2. 게시글 전체 embedding과 chunk embedding을 별도 테이블에 저장한다.
3. Qdrant는 vector 기반 1차 후보를 반환한다.
4. Java 서비스가 Qdrant 후보 안에서 BM25, RRF, keyword/guard term, metadata, chunk evidence를 결합해 재정렬한다.
5. 초안 생성은 강한 근거만 prompt source로 넣고, 직접 근거가 부족하면 fallback을 반환한다.

RepoLM에 적용할 때 중요한 점은 “검색 결과가 있다”와 “답변 근거로 쓸 만큼 충분하다”를 분리하는 것이다. 후보 검색은 넓게, 답변 생성은 엄격하게 가져가는 구조가 자연스러운 대화 품질을 만든다.

## 2. Chunking과 임베딩

HYUNJIN은 게시글 본문을 문단 우선으로 나누고, 기본 chunk 기준을 `1200자 / overlap 180자`로 둔다. 문단이 너무 길면 길이 기준으로 강제 분할한다.

RepoLM은 게시글보다 자료형이 다양하므로 그대로 복사하면 안 된다. 대신 다음 원칙만 가져온다.

- chunk 크기는 감이 아니라 평가 후보로 둔다.
- overlap은 경계 문맥 손실을 줄이기 위한 장치로 유지한다.
- chunk-level score는 주 검색기가 아니라 근거 보정 신호로 취급한다.
- 원문 단위 summary와 chunk 단위 evidence를 함께 둔다.
- indexing job은 retry와 failed 상태를 명확히 남긴다.

RepoLM에는 이미 Markdown/PDF/code/text별 chunk metadata와 parent/prev/next expansion이 있으므로, 다음 단계는 chunk size와 expansion policy를 evaluation candidate로 올리는 것이다.

## 3. Hybrid Retrieval

HYUNJIN의 핵심은 vector, BM25, RRF, metadata, chunk evidence를 한 번에 무작정 섞지 않고 단계별 역할을 나눈 점이다.

| 신호 | 역할 |
| --- | --- |
| Vector | 의미적으로 가까운 후보를 찾는다. |
| BM25 | 고유명사, API 이름, 에러 코드처럼 표면 단어가 중요한 질문을 잡는다. |
| RRF | vector rank와 BM25 rank를 점수 스케일 문제 없이 결합한다. |
| Metadata | category/tag 같은 사용자 맥락을 보정한다. |
| Guard term | 질문 핵심어와 무관한 후보를 낮춘다. |
| Chunk evidence | chunk 단위 직접 근거를 소폭 보강한다. |

RepoLM은 Postgres `pgvector`와 `ts_rank` 기반 hybrid search, 다중 query RRF, code-first trust policy를 갖고 있다. 부족한 부분은 검색 파라미터가 아직 제품 평가 단위로 노출되지 않았다는 점이다. `VECTOR_WEIGHT`, `KEYWORD_WEIGHT`, RRF k, top_k, context expansion 폭, docs alignment 정책을 설정 후보로 만들고 online 평가를 돌려야 한다.

## 4. Offline과 Online 평가 분리

HYUNJIN 문서에서 가장 중요한 교훈은 offline 점수가 곧 제품 성능이 아니라는 점이다.

- offline: MySQL/저장 데이터를 넓게 읽어 빠르게 후보 설정을 비교한다.
- online: 실제 API 서버를 띄우고 Qdrant, MySQL, OpenAI query embedding 경로를 모두 태운다.
- scenario: 실제 사용 질문과 화면 흐름에서 답변이 자연스러운지 확인한다.
- RAGAS: 생성 답변이 context에 충실한지 보조적으로 본다.

RepoLM도 같은 층위를 가져야 한다. 특히 repo 질문은 source/file scope, code-vs-doc trust, no-evidence 답변, conflict 답변, UML/ERD/dependency artifact까지 포함하므로 단순 retrieval metric만으로 충분하지 않다.

## 5. 지표 우선순위

HYUNJIN은 작성 보조 화면에서 상위 3-5개 추천이 중요하다는 제품 맥락 때문에 다음 순서를 둔다.

1. `MRR@5`: 첫 관련 결과가 얼마나 빨리 나오는가
2. `Hit@5`: 상위 5개 안에 관련 결과가 하나라도 있는가
3. `NDCG@5`: 관련 결과가 위쪽에 배치되는가
4. `Precision@5`: 상위 5개 중 노이즈가 얼마나 적은가
5. `Recall@5`: 전체 관련 결과 중 얼마나 회수했는가

RepoLM도 비슷하다. 사용자는 전체 레포의 모든 관련 파일을 원하기보다 “이 질문에 바로 쓸 수 있는 근거와 답”을 원한다. 따라서 code Q&A에서는 `MRR@5`, `NDCG@5`, citation file path 정확도를 우선 지표로 둔다.

## 6. 생성 Gate

HYUNJIN의 `RagDraftService`는 prompt에 넣을 source를 제한한다. 검색된 결과라도 score, matched terms, 위치/필수/anchor term 조건을 통과하지 못하면 사실 근거로 사용하지 않는다.

RepoLM에 맞춘 gate는 다음이어야 한다.

- 선택된 source/file scope 밖의 chunk는 답변과 tool read에서 제외한다.
- 소스코드 관련 질문은 repo docs보다 실제 code/schema/config chunk를 우선한다.
- docs는 code와 일치할 때 보조 근거로만 쓴다.
- 충돌하면 한쪽을 조용히 선택하지 않고 충돌과 양쪽 citation을 보여준다.
- 근거가 부족하면 일반론으로 때우지 않고 자료 내 확인 불가를 말한다.
- 여러 repo가 선택되고 질문이 모호하면 기준 repo를 되묻는다.

## 7. RepoLM에 바로 적용할 평가 하니스

HYUNJIN 방식을 RepoLM에 맞추면 다음 파일/데이터가 필요하다.

| 항목 | 내용 |
| --- | --- |
| `eval/repolm/retrieval-cases.json` | 질문, 선택 source/file scope, 기대 file path, 기대 chunk id 또는 symbol을 둔다. |
| `scripts/evaluate-repolm-retrieval.py` | `/api/notebooks/{id}/chat` 또는 내부 search service를 호출해 `Hit@K`, `MRR@K`, `NDCG@K`, `Precision@K`, `Recall@K`를 계산한다. |
| `scripts/evaluate-repolm-candidates.py` | top_k, vector/keyword weight, RRF, context expansion, trust policy 후보를 실제 API 경로에서 비교한다. |
| `eval/repolm/ragas` | 답변 생성 결과의 faithfulness, answer relevancy, context precision/recall을 측정한다. |
| `docs/woonyong/repolm-rag-scenarios.md` | 모호한 질문, 충돌, 근거 없음, artifact 생성, source 삭제 후 검색 제외 같은 제품 시나리오를 남긴다. |

## 8. 결론

HYUNJIN 브랜치가 RepoLM에 주는 가장 큰 기준은 “RAG를 만들었다”가 아니라 “실제 서비스 경로에서 실험하고, 숫자와 시나리오로 채택 여부를 결정한다”는 운영 방식이다. RepoLM은 이미 자료형별 chunking, scope filtering, code-first trust, artifact generation의 기반을 갖췄으므로 다음 병목은 검색/답변 품질을 지속 측정하는 evaluation loop다.
