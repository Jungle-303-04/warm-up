# 스킬 문서

이 문서는 프로젝트에서 다루는 스킬을 `docs/skills/`에서 빠르게 확인하기 위한 지도다.
스킬은 단순 키워드 목록이 아니라, 어떤 상황에서 어떤 문서를 보면 되는지까지 포함한다.

## Skill Map

| 영역 | 스킬 | 위치 | 사용 시점 |
| --- | --- | --- | --- |
| Full-stack | 언어 기초, 프론트엔드, 백엔드, 데이터 계층, 아키텍처 | `docs/woonyong/full-stack-tech-loadmap/` | 팀원이 기술 키워드의 의미와 사용 장면을 맞출 때 |
| AI Implementation | LLM Runtime, RAG, MCP, Agent, Memory, Evaluation, Python Architecture | `docs/woonyong/ai-implementation/` | AI 기능을 실제 구현 단위로 설계할 때 |
| Product | RepoPilot 제품 기획, 요구사항, 정보 구조, 로드맵 | `docs/woonyong/ai-dev-workspace/` | 제품 방향, MVP 범위, 기능 우선순위를 정할 때 |
| Operations | Notion 운영 항목, 회의, 일정, 작업 관리 | `docs/config/conventions.md` 및 Notion 팀 협업 허브 | 팀 일감과 회의 흐름을 관리할 때 |
| Git Workflow | 커밋, 브랜치, PR, 리뷰 기준 | `docs/config/conventions.md` | 협업 변경사항을 기록하고 병합할 때 |

## Full-stack Skills

기술 키워드를 외우는 것이 아니라, 각 기술이 해결하는 문제를 이해하는 데 집중한다.

- Language Basics: TypeScript, Java, Python, OOP, Functional Programming, Error Handling, Test Framework
- Frontend: React, Vue.js, Rendering, Component Design, State Management, UI Framework, Accessibility
- Backend: FastAPI, Spring Boot, NestJS, REST, gRPC, GraphQL, Auth, Realtime, Security, Queue, Caching
- Data Layer: PostgreSQL, MySQL, SQL, Data Modeling, Transaction, Reliability, Scalability
- Architecture: MVC, Layered, Modular Monolith, Clean Architecture, Hexagonal, ADR, Microservices, CQRS

## AI Implementation Skills

AI 기능은 모델 호출 자체보다 입력, 상태, 도구, 평가, 관측 가능성을 함께 설계한다.

- LLM Runtime: Responses API, Prompt Architecture, Structured Output, Function Calling, Streaming, Token Budget
- RAG: Parsing, Cleaning, Chunking, Embedding, Vector Store, Retrieval, Reranking, Citation, Evaluation
- MCP: Host, Client, Server, Tool, Resource, Prompt, Permission, Human Approval, Prompt Injection Defense
- Agent Orchestration: Workflow vs Agent, Agent State, Action Schema, Stop Conditions, LangGraph, Handoff
- Memory and Evaluation: Short-term Memory, Long-term Memory, Golden Dataset, Trace, Metrics, Cost Tracking
- Python Architecture: Modular Monolith, Ports and Adapters, Domain Model, Use Case, Repository, Unit of Work

## RepoPilot Product Skills

RepoPilot 관련 문서는 Notion, GitHub, 코드, 정적 뷰어를 연결하는 제품 관점에서 읽는다.

- Product Planning: 문제 정의, 사용자, MVP 컷라인
- Information Architecture: 페이지, 일감, 일정, 회의록, 위키의 공통 모델
- GitHub Workflow: 프로젝트, 이슈, 브랜치, PR, 에이전트 제안 흐름
- Collaboration UI: 실시간 편집과 읽기 전용 정적 뷰어의 역할 분리
- Security and Permissions: 초대, 권한, 퍼블리싱, RAG 접근 제어
- Agent and RAG: 코드-문서 연결 상태, stale/broken/suggested 판단

## Documentation Skill

문서는 아래 순서로 정리한다.

1. 목적을 한 문장으로 고정한다.
2. 독자가 바로 찾을 수 있는 위치에 둔다.
3. 키워드는 상위 개념 아래에 묶는다.
4. 구현 근거가 있으면 파일 경로 또는 공식 문서 링크를 남긴다.
5. 오래될 수 있는 내용은 마지막 갱신일 또는 검토 필요 상태를 남긴다.

## Operation Skill

팀 운영은 Notion의 단일 운영 DB를 기준으로 한다.

- 회의: 논의, 결정, 실행 항목의 출처
- 일정: 기간과 마감의 기준
- 작업: 담당자가 실행할 단위
- 담당자: 실제 수행 책임자
- 작성자: 항목을 만든 사람
- 참조자: 확인이 필요한 사람
- 상태: 대기, 진행, 종료, 보류

## Skill Update Rule

- 새 기술이 등장하면 바로 속성이나 DB를 늘리지 않는다.
- 먼저 관련 문서 위치를 정한다.
- 반복해서 쓰이는 기술만 `docs/skills/README.md`에 추가한다.
- 구현 코드가 생기면 해당 스킬 설명에 레포 경로를 연결한다.
- 팀 운영 규칙이 바뀌면 `docs/config/conventions.md`를 먼저 갱신한다.
