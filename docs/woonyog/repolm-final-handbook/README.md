# RepoLM 최종 구현 해설서

이 폴더는 현재 `woonyong` 브랜치 기준 RepoLM 구현을 기술 문서로 정리한 핸드북이다.
설명은 "개념 문법 → 현재 코드 구현 → 실행 흐름 → 한계와 개선 지점" 순서로 읽을 수 있게 구성했다.

## 문서 목록

1. [MCP 구현과 사용법](./01-mcp-implementation.md)
   - `backend/app/mcp/server.py`, `backend/app/mcp/client.py`
   - stdio MCP 서버, LangChain 도구 변환, LangGraph 연결 방식

2. [AI 에이전트와 LLM 처리 흐름](./02-ai-agent-and-llm-flow.md)
   - 채팅 입력, planner, RAG 검색, tool loop, LangGraph proposal graph
   - 어떤 기준으로 분기하고 어떤 도구를 여는지

3. [RAG, 임베딩, SQL 저장 구조](./03-rag-sql-indexing.md)
   - 자료형별 청킹, 임베딩 한 사이클, pgvector/tsvector 검색
   - 노트북 SQL 저장소와 레포 RAG SQL 저장소의 역할

4. [동기화, 스케줄러, 라이프사이클](./04-sync-scheduler-lifecycle.md)
   - GitHub repo 수집, diff, soft delete, cleanup, worker polling
   - 색인 상태가 UI와 API로 이어지는 방식

5. [서비스 아키텍처와 트랜잭션 흐름](./05-service-architecture-and-transactions.md)
   - 전체 서비스 컴포넌트, 요청별 트랜잭션 흐름, 프론트 상호작용
   - 왜 이런 구조로 개발했는지와 검토 기준

## 현재 구현의 핵심 결론

- RepoLM의 일반 채팅은 `ChatService`가 deterministic planner로 라우팅하고, 필요할 때 RAG 검색과 제한된 인프로세스 도구를 사용한다.
- LangGraph는 일반 채팅 본류가 아니라 `pipeline` 제안 생성 그래프에서 사용한다.
- MCP는 `backend/app/mcp/server.py`에 stdio 서버로 구현되어 있고, `backend/app/mcp/client.py`가 이를 LangChain `StructuredTool`로 변환한다.
- RAG는 자료형별 chunker가 만든 metadata-rich chunk를 SQL/pgvector에 저장하고, vector score와 keyword score를 결합해 검색한다.
- SQL은 노트북 제품 데이터와 레포 RAG 동기화 데이터를 모두 영속화한다. ORM이 중심이며, pgvector/tsvector 같은 Postgres 고유 검색 기능만 SQLAlchemy expression으로 사용한다.
- 프론트는 선택된 source/file scope를 요청에 포함하고, 채팅 중 추가 입력은 큐에 담아 순차 처리하도록 설계되어 있다.

