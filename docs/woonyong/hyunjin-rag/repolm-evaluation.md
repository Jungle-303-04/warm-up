# HYUNJIN 기준 RepoLM RAG 평가

이 평가는 HYUNJIN 브랜치의 RAG 방법론을 기준으로 현재 RepoLM 구현을 점검한 결과다. RepoLM 로컬 코드는 `woonyong` 브랜치의 현재 상태를 기준으로 봤고, HYUNJIN 외부 자료는 `ca56e75e115987b095e4806cf81f234a1d371465` 커밋만 사용했다.

## 총평

RepoLM은 RAG 기능의 구조적 기반은 많이 갖췄다. 특히 source/file scope filtering, 자료형별 chunk metadata, parent/prev/next context expansion, code-first trust, artifact generator는 HYUNJIN보다 더 일반적인 레포 분석 서비스에 맞게 확장되어 있다.

다만 사용자가 체감하는 “왜 SQL/RAG를 넣었는데 자연스럽게 대답하지 못하나”의 핵심 원인은 evaluation loop 부족이다. 현재는 기능 테스트와 타입/린트 검증은 강해졌지만, 실제 질문별 기대 근거를 두고 검색 품질과 답변 충실도를 반복 측정하는 장치가 아직 제품 루프에 들어오지 않았다.

## 영역별 평가

| 영역 | 상태 | 근거 | 보완점 |
| --- | --- | --- | --- |
| 자료 수집/chunking | 좋음 | Markdown/PDF/code/text chunk metadata, parent/prev/next link, code summary chunk가 있다. | chunk size, overlap, expansion 폭을 평가 후보로 관리해야 한다. |
| Hybrid retrieval | 보통 이상 | `pgvector` 후보와 `ts_rank` keyword 후보를 섞고, 다중 query RRF를 쓴다. | vector/keyword weight, RRF k, top_k가 제품 실험값으로 관리되지 않는다. |
| Scope enforcement | 좋음 | `source_ids`, `file_paths`가 search와 tool read에 전달된다. | 평가 케이스로 선택되지 않은 source/file 누출을 계속 검증해야 한다. |
| Code-first trust | 좋음 | repo docs/README보다 실제 code/schema/config를 우선하도록 chat/artifact prompt와 ranking을 강화했다. | 답변 prompt에 evidence kind를 더 구조적으로 넘기면 LLM의 임의 해석을 줄일 수 있다. |
| Conflict/no-evidence | 좋음 | 충돌 감지와 근거 없음 답변 흐름이 있다. | 충돌 유형별 golden scenario가 필요하다. |
| Artifact generation | 좋음 | UML, ERD, dependency, change summary가 code facts 기반 deterministic fallback을 갖는다. | 생성물 품질 평가 케이스와 Mermaid 렌더 검증이 필요하다. |
| Indexing lifecycle | 보통 이상 | SQL 기반 progress, chunk count, 상태 노출 흐름이 있다. | 장시간 indexing heartbeat, stale running 복구, 실패 원인 분류를 평가에 포함해야 한다. |
| RAG 성능 측정 | 부족 | 단위 테스트는 통과하지만 HYUNJIN식 retrieval metric/RAGAS/online ablation이 없다. | 가장 먼저 보강해야 할 영역이다. |

## HYUNJIN 대비 가장 큰 차이

HYUNJIN은 최종 답을 “느낌”으로 고르지 않는다. 실제 API 경로에서 후보 설정을 바꿔 `Precision@5`, `Recall@5`, `MRR@5`, `NDCG@5`, `Hit@5`를 계산하고, RAGAS와 scenario 평가를 보조로 사용한다.

RepoLM은 현재 다음 질문에 숫자로 답할 수 없다.

- 이 질문에서 정답 파일이 top5 안에 들어오는가?
- 첫 관련 chunk가 몇 번째에 나오는가?
- docs chunk가 code chunk를 밀어내는 경우가 얼마나 되는가?
- parent/prev/next expansion이 답변 품질을 올리는가, 아니면 노이즈를 늘리는가?
- 여러 repo 선택 시 되묻기 정책이 실제로 오답을 줄이는가?
- UML/ERD/dependency/change summary가 기대 파일과 symbol을 반영하는가?

따라서 “벡터 DB와 SQL을 활용하지 못한다”는 체감은 검색 구현 부재보다 측정 가능한 선택 루프 부재에 가깝다.

## RepoLM 전용 평가셋 제안

`eval/repolm/retrieval-cases.json`은 최소한 다음 유형을 포함해야 한다.

| 유형 | 기대값 |
| --- | --- |
| 구현 질문 | 실제 source file path와 symbol chunk가 top5 안에 있어야 한다. |
| docs/code 충돌 | code 근거를 우선하고 충돌을 표시해야 한다. |
| 근거 없음 | 검색 hit가 약하면 자료 내 확인 불가로 답해야 한다. |
| 여러 repo 선택 | 모호하면 기준 repo를 되묻고, 같은 repo 여러 branch면 branch별 비교 답변을 해야 한다. |
| 파일 scope 제한 | 선택되지 않은 file path가 retrieval/tool read 결과에 나오면 실패다. |
| URL/문서 질문 | source kind에 맞는 chunk와 citation이 나와야 한다. |
| UML/ERD/dependency | Mermaid에 기대 class/table/module edge가 포함되어야 한다. |
| 변경 요약 | docs보다 code fact가 요약의 1차 근거여야 한다. |

## 지표 설계

RepoLM의 retrieval 지표는 HYUNJIN의 top5 지표를 가져오되, 레포 분석 서비스에 맞춰 보강한다.

| 지표 | 의미 |
| --- | --- |
| `Hit@5` | 기대 file/symbol/chunk가 top5 안에 하나라도 있는지 |
| `MRR@5` | 첫 기대 근거가 몇 번째에 나오는지 |
| `NDCG@5` | 기대 근거가 상위에 모여 있는지 |
| `Precision@5` | top5 citation 중 질문과 무관한 노이즈가 적은지 |
| `Recall@5` | 기대 근거 전체 중 top5에 들어온 비율 |
| `CodeEvidence@5` | code 질문에서 code/schema/config chunk가 docs보다 앞서는지 |
| `ScopeLeak` | 선택 밖 source/file이 노출됐는지 |
| `GroundedAnswer` | 답변 문장이 citation으로 뒷받침되는지 |

## 우선 구현 순서

1. `eval/repolm/retrieval-cases.json`을 만든다.
2. 내부 `ChunkStore.search()`를 직접 호출하는 빠른 offline 평가 스크립트를 만든다.
3. 실제 API `/api/notebooks/{id}/chat`을 호출하는 online 평가 스크립트를 만든다.
4. 후보군을 `top_k`, vector/keyword weight, RRF k, context expansion, code-first docs filtering으로 나눠 비교한다.
5. RAGAS 또는 LLM judge로 answer faithfulness와 context precision/recall을 측정한다.
6. artifact 유형별 Mermaid/Markdown 구조 검증을 추가한다.
7. 평가 결과를 `docs/woonyong/repolm-evaluations/`에 날짜별로 저장한다.

## 제품 UX 기준

HYUNJIN의 평가 방식은 RepoLM UX에도 직접 연결된다.

- indexing 중이면 실패로 단정하지 말고 heartbeat와 진행률을 보여준다.
- 소스 등록 실패를 빨간 내부 오류처럼 노출하지 말고, 사용자 행동 가능한 상태 메시지로 바꾼다.
- 여러 repo가 선택된 모호한 질문은 되묻는다.
- 같은 repo의 여러 branch가 선택되면 branch별 차이를 나눠 답한다.
- code 질문은 docs보다 실제 code를 우선하고, docs는 일치할 때 보조 근거로 보여준다.
- 답변에는 citation file path와 line/chunk metadata를 계속 노출한다.

## 결론

RepoLM은 “RAG를 못 쓰는 상태”라기보다 “RAG 품질을 숫자로 조절하는 운영 루프가 아직 부족한 상태”다. HYUNJIN 기준으로 다음 완성 기준은 명확하다.

1. 검색/답변/artifact에 대한 golden cases가 있다.
2. offline과 online 평가가 분리되어 있다.
3. 최종 설정은 실제 API 경로의 `MRR@5`, `NDCG@5`, `Precision@5`, `Hit@5`로 채택한다.
4. 생성 답변은 RAGAS나 LLM judge로 faithfulness를 확인한다.
5. 평가 결과가 문서와 CI/운영 체크에 남는다.

이 루프가 들어가야 SQL과 vector DB가 단순 저장소가 아니라 제품 품질을 계속 끌어올리는 장치가 된다.
