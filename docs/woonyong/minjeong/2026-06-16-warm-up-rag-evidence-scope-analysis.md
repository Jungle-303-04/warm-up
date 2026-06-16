# 2026-06-16 warm-up RAG 근거 범위/중복 저장 분석

## 범위

- 사람: [민정](./README.md)
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: [`842d495`](https://github.com/Jungle-303-04/warm-up/commit/842d49559f83cd89d0500049efe80909500d99f5)
- 커밋 메시지: `fix: skip duplicate RAG index storage`
- 날짜 범위: `2026-06-16`

## 하루 요약

민정은 `/rag/ask` 답변이 특정 repository/branch/commit 기준의 evidence 안에서만
나오도록 범위를 좁혔다. 이후 LangGraph answer flow에 evidence 유무 분기를 넣고,
같은 repository/branch/commit 조합이 이미 SQL에 있으면 RAG 인덱싱 저장을 재사용하도록
중복 저장 방지를 추가했다.

## 시간대별 작업 흐름

### 02:10 - `d0a73de feat: scope RAG ask by repository commit`

- `RagAskRequestDTO`에 repository/branch/commit 기준을 명확히 했다.
- vector search가 `repository_full_name`, `branch`, `commit_sha` metadata filter를 사용한다.
- SQL에서 최신/정확한 index run을 찾고, 그 run 기준으로 vector evidence를 검색한다.
- Bruno와 frontend 요청도 commit 기준 질문 흐름에 맞췄다.

### 03:13 - `1865d09 refactor: branch RAG answer graph on evidence`

- `RagAnswerGraph`가 vector 검색 후 evidence 존재 여부로 분기한다.
- 근거가 있으면 LLM answer를 생성하고, 근거가 없으면 기본 no-evidence 답변을 만든다.
- LLM이 근거 없이 추측하는 것을 막는 방향이다.

### 04:13 - `842d495 fix: skip duplicate RAG index storage`

- `RagIndexService.find_existing_run()`으로 repository/branch/commit이 같은 기존 run을 찾는다.
- 기존 run이 있으면 GitHub 파일 수집, chunk 생성, SQL/vector 저장을 다시 하지 않고 `reused=True`로 응답한다.
- vector/SQL repository에 중복 확인과 count 조회가 보강됐다.
- frontend와 Bruno도 reused 응답을 볼 수 있게 수정했다.

## 무엇을 고려했는가

- RAG 답변은 사용자가 보는 코드 버전과 같은 commit의 evidence에서만 나와야 한다.
- run_id는 사용자가 직접 외우는 입력값이 아니라 저장 이력 추적용이고, 실제 신뢰 기준은 repository/branch/commit이다.
- evidence가 없으면 LLM을 호출하지 않거나 추측 답변을 막아야 한다.
- 같은 commit을 반복 인덱싱하면 SQL/vector DB가 불필요하게 커지므로 재사용해야 한다.

## 잘한 점

- commit 기준 필터를 넣은 것은 RAG 품질에서 핵심이다. stale code evidence 위험을 줄인다.
- no-evidence branch를 graph에 명시한 점은 LLM hallucination 방지에 직접 도움이 된다.
- duplicate index reuse는 비용과 저장소 팽창을 줄인다.
- docs/rag_ask_flow.md에 현재 구현 범위와 아직 남은 agent workflow 범위를 분리해 쓴 점이 좋다.

## 부족하거나 위험한 점

- 중복 저장 방지는 동시 요청 race condition까지 막는 DB unique constraint가 필요하다.
- vector DB upsert와 SQL transaction 사이의 부분 실패 보상 전략이 아직 명확하지 않다.
- commit_sha가 없는 요청에서 "최신 run" 선택 기준이 사용자 기대와 다를 수 있다.
- no-evidence branch는 기본 답변만 있으므로 재검색, query rewrite, SQL fallback은 아직 없다.
- LangGraph 도입은 구조상 진전이지만 현재 graph는 아직 단순 분기 RAG workflow다.

## 개선 방향

1. `repository_full_name + branch + commit_sha`에 DB unique constraint 또는 idempotency lock을 둔다.
2. SQL 저장 성공 후 vector 저장 실패, vector 저장 성공 후 SQL commit 실패 보상 기준을 정한다.
3. `/rag/ask` 테스트를 추가한다.
   - exact commit evidence found
   - no evidence
   - duplicate index reused
   - branch only latest run
4. no-evidence branch에 SQL keyword fallback 또는 query rewrite를 붙일지 결정한다.
5. Agent와 RAG answer graph의 경계를 문서와 route 이름에서 계속 분리한다.

## 사용자가 지금 도울 수 있는 말

- "commit 기준으로 RAG 답변 범위를 좁힌 건 맞는 방향이야. 이제 중복 저장 방지는 unique constraint와 동시 요청 테스트로 고정해야 해."
- "LangGraph를 쓴다고 바로 agent가 되는 건 아니야. 지금은 RAG answer graph고, tool 실행 agent는 별도 단계로 분리해서 보자."
- "SQL/vector 저장 중 하나만 성공하는 실패 케이스를 반드시 정해야 해."

