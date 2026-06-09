# Python 백엔드 아키텍처

## 결정

FastAPI, PostgreSQL, Redis worker, 명확한 domain boundary를 가진 modular monolith로 시작한다. Microservice로 시작하지 않는다.

## Runtime Model

```text
FastAPI API server
짧은 request/response 작업

Realtime server
presence와 collaborative editing

Worker process
GitHub sync, indexing, publish, AI proposal 처리

PostgreSQL
app state의 source of truth

Redis
queue/cache/presence support
```

## 추천 구조

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── services/
│   │   ├── workspace.py
│   │   ├── project.py
│   │   ├── item.py
│   │   ├── github.py
│   │   ├── code_index.py
│   │   ├── publish.py
│   │   ├── rag_index.py
│   │   └── agent.py
│   ├── db/
│   ├── workers/
│   └── main.py
└── tests/
```

## Layering

```text
API layer
  ↓
Application use cases
  ↓
Domain models/services
  ↓
Ports
  ↓
Infrastructure adapters
```

FastAPI route는 GitHub/indexing/publishing logic을 직접 수행하지 않고 use case를 호출한다.

## Core Modules

- `workspace`: member, role, settings
- `project`: project와 repo attachment
- `item`: WorkspaceItem, properties, views
- `github`: GitHub App, issues, PRs, permissions
- `code_index.py`: files, symbols, code references
- `publish.py`: static export jobs
- `rag_index.py`: retrieval chunks와 context packs
- `agent.py`: proposals와 approvals

## Background Work

Worker job으로 처리할 것:

- GitHub sync
- repo indexing
- vector indexing
- static publish
- stale link detection
- AI proposal generation

이 작업들은 HTTP handler 안에서 실행하지 않는다.

## FastAPI Concurrency Rules

- `async` handler는 I/O 작업에 적합하다.
- CPU-heavy parsing은 worker 또는 process pool로 보낸다.
- 여러 Uvicorn worker는 memory를 공유하지 않는다.
- 공유 state는 Python global이 아니라 PostgreSQL/Redis에 둔다.
- 긴 job은 idempotency와 retry handling이 필요하다.

## Python Modeling

사용:

- API schema와 validation: Pydantic
- domain value: 필요할 때 dataclass 또는 simple class
- persistence: SQLAlchemy model
- port/interface: Protocol
- application flow: use case class/function

피할 것:

- 모든 로직을 router에 넣기
- DB model만 감싼 빈약한 service
- 성급한 service 분리
- global mutable state

## Test Layout

현재 테스트는 소스 경로를 미러링한다.

```text
app/main.py                 -> tests/test_main.py
app/pipeline.py             -> tests/test_pipeline.py
app/schemas/pipeline.py     -> tests/schemas/test_pipeline.py
app/services/repo_sync.py   -> tests/services/test_repo_sync.py
app/services/code_index.py  -> tests/services/test_code_index.py
app/services/rag_index.py   -> tests/services/test_rag_index.py
app/services/agent.py       -> tests/services/test_agent.py
app/services/approval.py    -> tests/services/test_approval.py
app/services/publish.py     -> tests/services/test_publish.py
app/services/pipeline.py    -> tests/services/test_pipeline.py
app/workers/runner.py       -> tests/workers/test_runner.py
```

`__init__.py` 없이 같은 basename의 테스트 파일을 여러 폴더에 둘 수 있도록 pytest는 `--import-mode=importlib`로 실행한다.

## Key Tables

```text
workspaces
projects
repositories
workspace_items
views
github_issue_links
code_references
doc_code_links
publish_snapshots
agent_proposals
audit_events
retrieval_chunks
```

## Testing

P0 test:

- permission filtering
- item type/property behavior
- GitHub issue proposal creation
- code-doc link status 전이
- static publish visibility
- RAG retrieval permission boundary

## Architecture Assets

Diagram이 필요하면 현재 model에서 생성한다. 제품 기획과 따로 노는 UML 문서를 별도로 유지하지 않는다.
