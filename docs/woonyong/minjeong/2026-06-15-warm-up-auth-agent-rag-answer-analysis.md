# 2026-06-15 warm-up Auth/Agent/RAG 답변 분석

## 범위

- 사람: [민정](./README.md)
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 대상 커밋: `7b51bd9 docs: clarify RAG ask boundaries and run ids`
- 날짜 범위: `2026-06-15`

## 하루 요약

민정은 RAG indexing을 SQL/vector DB 저장 구조로 확장했고, GitHub OAuth/JWT 기반
auth, repository RAG answer workflow, agent chat scaffold, frontend OAuth/RAG
테스트 화면까지 한 번에 넓혔다. 중간에 `domains/*` 구조를 `auth`, `board`,
`github`, `rag`, `agent` top-level module로 재배치하면서 ports/external/service
계층을 명확히 하려는 시도가 보인다.

## 시간대별 작업 흐름

### 01:04 - `a5c4b66 feat: store RAG indexes in SQL and vector DB`

- `RagIndexRun`, file snapshot, chunk, skipped file 모델을 추가했다.
- SQL repository와 Chroma vector repository를 추가했다.
- OpenAI embedding service를 붙였다.
- Bruno collection으로 board/RAG/system API 호출 예시를 추가했다.
- RAG가 "메모리에서 chunk 생성"을 넘어 저장 가능한 인덱싱 시스템으로 이동했다.

### 01:41 - `6b59517 refactor: align layered pipeline and auth structure`

- GitHub OAuth, JWT, auth repository/service/router를 추가했다.
- board/github/rag를 api/application/domain/infrastructure 계층으로 재배치했다.
- `dependency_injector`, ports, service 구조를 도입했다.
- 의도는 FastAPI 프로젝트를 기능별 script 묶음에서 계층형 backend로 재구성하는 것이다.

### 01:55 - `53dfba1 feat: add github oauth test console`

- frontend에 GitHub OAuth 테스트 UI를 추가했다.
- backend auth 흐름을 사용자가 눈으로 확인할 수 있는 console을 만든 것으로 보인다.

### 02:00 - `ca6152c fix: localize oauth login screen`

- OAuth login 화면을 한국어 중심으로 정리했다.
- CSS와 JSX를 줄여 화면 복잡도를 낮췄다.

### 02:42 - `0574d07 feat: add repository RAG answer workflow`

- `/rag/ask` 성격의 repository RAG 답변 흐름을 추가했다.
- `answer_service.py`, vector search, LLM answer generation, frontend repository workspace를 연결했다.
- GitHub repository content 수집과 RAG answer UI가 한 흐름으로 이어지기 시작했다.

### 04:12 - `266b5c3 Refactor backend modules and add agent chat scaffold`

- `domains/*`를 top-level `auth`, `board`, `github`, `rag`, `agent` module로 재배치했다.
- `ports.py`, `external`, `service`, `api`, `domain` 구조를 정리했다.
- agent chat scaffold를 추가했다.
- frontend도 `features/auth`, `features/repository`, `shared/api`, `shared/auth`로 분리했다.

### 21:17 - `6b07845 docs: add RAG study diagrams and notes`

- `docs/rag_study.md`, `docs/rag_ask_flow.md`, PlantUML diagram을 추가했다.
- RAG 구현을 학습/설명 가능한 문서로 정리했다.

### 21:51 - `804d34f refactor: route RAG answer flow through LangGraph`

- RAG answer flow를 `RagAnswerGraph`로 옮겼다.
- `retrieve_vector -> generate_answer -> build_response` 흐름을 graph로 표현했다.

### 23:22 - `7b51bd9 docs: clarify RAG ask boundaries and run ids`

- `/rag/ask`가 완성형 agent workflow가 아니라 SQL 기준 run 조회와 vector 검색, LLM 답변에 가까움을 문서화했다.
- run_id와 repository/branch/commit 기준의 역할 차이를 설명했다.

## 무엇을 고려했는가

- RAG evidence는 SQL 원문 저장과 vector DB 검색을 같이 가져가야 추적성과 검색성을 모두 얻는다고 봤다.
- GitHub OAuth와 JWT를 도입해 사용자 GitHub token으로 repository를 수집하려 했다.
- 기능별 module을 ports/service/external로 나눠 테스트 가능한 구조를 만들려 했다.
- RAG answer는 agent 전체가 아니라 "저장된 근거 검색 + LLM 답변"으로 범위를 제한하려 했다.

## 잘한 점

- SQL/vector 이중 저장 구조는 RAG 운영에 필요한 추적성을 준다.
- repository/branch/commit 기준을 잡은 것은 stale evidence 문제를 줄인다.
- ports와 external 분리는 외부 API, DB, LLM 교체 가능성을 높인다.
- LangGraph를 도입하면서 RAG answer flow의 분기 지점을 명시하기 시작했다.
- 문서와 diagram을 추가해 구현 흐름을 설명 가능한 형태로 만들었다.

## 부족하거나 위험한 점

- 하루에 auth, RAG, frontend, agent, module refactor가 동시에 들어와 회귀 위험이 크다.
- 실제 테스트 파일이 보이지 않는다.
- OAuth/JWT/LLM/vector DB는 env와 secret이 필요하므로 `.env.example`과 실패 메시지 기준이 중요하다.
- agent scaffold는 echo/memory 수준이라 실제 tool execution이나 planner로 보기는 어렵다.
- LangGraph 사용은 맞지만, 아직 graph는 단순 RAG answer flow에 가깝다.

## 개선 방향

1. Auth login/callback/current-user 최소 테스트를 추가한다.
2. RAG indexing SQL/vector 저장 통합 테스트를 추가한다.
3. `/rag/ask`의 no evidence, evidence found, invalid repository 케이스를 테스트한다.
4. `.env.example`에 GitHub OAuth, JWT, OpenAI, Chroma 설정을 명시한다.
5. Agent scaffold가 실제 agent인지 echo chat인지 문서와 이름으로 분리한다.

