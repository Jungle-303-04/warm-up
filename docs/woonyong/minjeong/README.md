# 민정

이 폴더는 민정의 `minjeong` 브랜치 구현 분석, 하루 단위 작업 아카이브,
클래스 단위 시각화 자료를 모아두는 공간이다.

파일명과 경로는 저장소 관리 편의를 위해 영어로 유지하지만, 문서 제목과 본문은
한국어로 작성한다.

## 현재 스냅샷

- 저장소: `Jungle-303-04/warm-up`
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: `842d495 fix: skip duplicate RAG index storage`
- 확인 시각: `2026-06-16 20:00:37 +09:00`

## 아카이브

- [민정 warm-up 커밋 진화 분석](./commit-evolution-analysis.md)
- [2026-06-11 warm-up Board 모델 분석](./2026-06-11-warm-up-board-model-analysis.md)
- [2026-06-12 warm-up Board 생성 응답 흐름 분석](./2026-06-12-warm-up-board-create-response-analysis.md)
- [2026-06-13 warm-up Board DB 저장 흐름 분석](./2026-06-13-warm-up-board-db-insert-analysis.md)
- [2026-06-14 warm-up RAG/GitHub 인덱싱 분석](./2026-06-14-warm-up-rag-github-indexing-analysis.md)
- [2026-06-15 warm-up Auth/Agent/RAG 답변 분석](./2026-06-15-warm-up-auth-agent-rag-answer-analysis.md)
- [2026-06-16 warm-up RAG 근거 범위/중복 저장 분석](./2026-06-16-warm-up-rag-evidence-scope-analysis.md)

## 구현 기준 메모

- [Board API 검증 실패 상태 코드 기준](./board-api-validation-status-policy.md): `400`, `422`, `409`를 나누는 기준

## 시각 자료

- [현재 클래스 UML](./class-uml.md): `842d495` 기준 backend 계층, RAG 인덱싱/답변 흐름, SQLAlchemy 모델 관계를 Mermaid로 정리한 자료

## 구현 읽기

최신 구현은 초기 `Board` CRUD를 넘어 GitHub OAuth, repository RAG indexing,
SQL/vector 저장, repository/branch/commit 범위의 RAG ask, LangGraph 기반 답변
흐름, agent chat scaffold까지 확장됐다.

주요 진입점은 다음과 같다.

- `backend/app/main.py`
- `backend/app/container.py`
- `backend/app/board/api/router.py`
- `backend/app/board/service/board_service.py`
- `backend/app/board/external/repository.py`
- `backend/app/auth/api/router.py`
- `backend/app/auth/service/auth_service.py`
- `backend/app/auth/external/github_oauth_client.py`
- `backend/app/github/service/github_service.py`
- `backend/app/github/external/repository.py`
- `backend/app/rag/api/router.py`
- `backend/app/rag/service/index_service.py`
- `backend/app/rag/service/pipeline.py`
- `backend/app/rag/service/answer_service.py`
- `backend/app/rag/service/answer_graph.py`
- `backend/app/rag/external/sql_repository.py`
- `backend/app/rag/external/vector_repository.py`
- `backend/app/agent/service/chat_service.py`
- `backend/app/agent/external/echo_responder.py`
- `frontend/src/features/auth`
- `frontend/src/features/repository`
- `docs/rag_ask_flow.md`
- `docs/rag_study.md`
- `bruno/warm-up-api`

현재 보이는 설계 방향은 기능별 top-level module과 ports/service/external 계층을
사용하는 FastAPI 백엔드다.

- `api`: HTTP router와 request/response DTO
- `service`: use case와 orchestration
- `domain`: 순수 도메인 helper, chunker, classifier, identity/citation
- `external`: SQLAlchemy, GitHub API, Chroma, OpenAI, in-memory store 같은 외부 의존성
- `container.py`: dependency-injector 기반 조립 위치

핵심 변화는 RAG 답변이 단순 vector search가 아니라 `repository_full_name`,
`branch`, `commit_sha` 기준 evidence로 제한되기 시작했다는 점이다. 같은
repository/branch/commit 조합은 기존 index run을 재사용해 `reused=True`로
응답하도록 보강됐다.

## RAG/Agent/MCP 관점

초기에는 Board 모델만 있었기 때문에 RAG, Agent, MCP 실행 기록을 담기에는
모델이 부족했다. 최신 브랜치에서는 `RagIndexRun`, `RagFileSnapshot`,
`RagChunk`, `RagSkippedFile`이 생겨 RAG 인덱싱 결과를 Board와 분리해 저장하는
방향으로 바뀌었다. 이 방향은 적절하다.

다만 아직 `agent` module은 `EchoAgentResponder`와 `InMemoryChatStore` 중심의
chat scaffold다. 현재 구현을 완성형 agent나 MCP tool executor로 부르기보다는,
RAG answer graph와 별도인 agent 실험 입구로 보는 편이 정확하다.

## 계속 봐야 할 지점

- RAG indexing과 `/rag/ask` 통합 테스트 부재
- GitHub OAuth/JWT/OpenAI/Chroma 설정을 설명하는 `.env.example` 부재
- `repository_full_name + branch + commit_sha` 중복 방지의 DB unique constraint 부재
- SQL 저장과 vector 저장 중 하나만 성공했을 때의 보상 전략 부재
- `latest run` 선택 기준과 사용자가 기대하는 commit 기준의 차이
- agent scaffold와 RAG answer graph의 경계
- Board CRUD의 기존 테스트 공백, N+1 query 위험, validation status 정책
