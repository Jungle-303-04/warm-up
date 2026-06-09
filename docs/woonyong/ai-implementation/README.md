# AI Implementation Roadmap

이 문서는 AI 기능 구현을 위한 루트 인덱스다.  
루트에는 전체 키워드 트리와 링크만 두고, 자세한 설명은 각 하위 문서에서 다룬다.

## 참고한 공식 문서

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/create?api-mode=responses)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling?api-mode=responses)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat)
- [OpenAI Conversation State](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph)
- [LangGraph Durable Execution](https://docs.langchain.com/oss/python/langgraph/durable-execution)
- [LangGraph Agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [Model Context Protocol Concepts](https://modelcontextprotocol.io/docs/concepts)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [pgvector](https://github.com/pgvector/pgvector)

## 문서 목록

- [01. LLM Runtime](./01-llm-runtime.md)
- [02. RAG](./02-rag.md)
- [03. MCP](./03-mcp.md)
- [04. Agent Orchestration](./04-agent-orchestration.md)
- [05. Memory, Evaluation, Observability](./05-memory-evaluation-observability.md)
- [06. Python Architecture](./06-python-architecture.md)

## 키워드 트리

```text
AI Implementation
├── LLM Runtime
│   ├── Responses API
│   ├── Prompt Architecture
│   ├── Structured Output
│   ├── Function Calling
│   ├── Streaming
│   ├── Conversation State
│   ├── Embedding
│   ├── Token Budget
│   ├── LLM Runtime Interface
│   └── Failure Handling
├── RAG
│   ├── Data Source
│   ├── Parser
│   ├── Cleaning
│   ├── Chunking
│   ├── Metadata
│   ├── Embedding
│   ├── Vector Store
│   ├── Retrieval
│   │   ├── Vector Search
│   │   ├── Keyword Search
│   │   ├── Hybrid Search
│   │   ├── Metadata Filtering
│   │   ├── Query Rewriting
│   │   ├── Multi Query
│   │   ├── Parent-Child Retrieval
│   │   └── Reranking
│   ├── Context Packing
│   ├── Answer Generation
│   ├── Citation
│   └── RAG Evaluation
├── MCP
│   ├── MCP Host
│   ├── MCP Client
│   ├── MCP Server
│   ├── Tool
│   ├── Resource
│   ├── Prompt
│   ├── JSON-RPC
│   ├── FastMCP
│   ├── Permission
│   ├── API Key Strategy
│   ├── Human Approval
│   └── Prompt Injection Defense
├── Agent Orchestration
│   ├── Workflow vs Agent
│   ├── Agent State
│   ├── Direct Agent Loop
│   ├── Action Schema
│   ├── Stop Conditions
│   ├── LangGraph
│   ├── Durable Execution
│   ├── Human-in-the-loop
│   ├── Manager Pattern
│   ├── Handoff Pattern
│   ├── Agent Policy
│   └── Agent Run Storage
├── Memory, Evaluation, Observability
│   ├── Short-term Memory
│   ├── Long-term Memory
│   ├── Memory Write Policy
│   ├── Memory Retrieval
│   ├── RAG Evaluation
│   ├── Agent Evaluation
│   ├── Golden Dataset
│   ├── Trace
│   ├── Metrics
│   ├── Cost Tracking
│   └── Debug Dashboard
└── Python Architecture
    ├── Modular Monolith
    ├── Layered Architecture
    ├── Ports and Adapters
    ├── OOP Boundary
    ├── Domain Model
    ├── Use Case
    ├── Repository
    ├── Unit of Work
    ├── Dependency Injection
    ├── Error Model
    ├── Package Structure
    └── Test Strategy
```

## 키워드 링크

### LLM Runtime

- [LLM Runtime](./01-llm-runtime.md)
- [Responses API](./01-llm-runtime.md#responses-api를-중심으로-보는-이유)
- [Prompt Architecture](./01-llm-runtime.md#prompt-구성)
- [Structured Output](./01-llm-runtime.md#structured-output)
- [Function Calling](./01-llm-runtime.md#function-calling)
- [Streaming](./01-llm-runtime.md#streaming)
- [Conversation State](./01-llm-runtime.md#responses-api를-중심으로-보는-이유)
- [Embedding](./02-rag.md#embedding)
- [Token Budget](./01-llm-runtime.md#token-budget)
- [LLM Runtime Interface](./01-llm-runtime.md#llm-runtime-인터페이스)
- [Failure Handling](./01-llm-runtime.md#실패-처리)

### RAG

- [RAG](./02-rag.md)
- [Ingestion Pipeline](./02-rag.md#ingestion-pipeline)
- [Data Source](./02-rag.md#source)
- [Parser](./02-rag.md#parser)
- [Cleaning](./02-rag.md#cleaning)
- [Chunking](./02-rag.md#chunking)
- [Embedding](./02-rag.md#embedding)
- [Vector Store](./02-rag.md#vector-store)
- [Retrieval](./02-rag.md#retrieval)
- [Vector Search](./02-rag.md#vector-search)
- [Keyword Search](./02-rag.md#keyword-search)
- [Hybrid Search](./02-rag.md#hybrid-search)
- [Context Packing](./02-rag.md#context-packing)
- [Answer Generation](./02-rag.md#answer-generation)
- [RAG Evaluation](./02-rag.md#rag-evaluation)
- [RAG Failure Patterns](./02-rag.md#rag-실패-패턴)

### MCP

- [MCP](./03-mcp.md)
- [MCP Host / Client / Server](./03-mcp.md#mcp-host--client--server)
- [Tool / Resource / Prompt](./03-mcp.md#tool--resource--prompt)
- [MCP Tool Design](./03-mcp.md#mcp-tool-설계)
- [Tool Output Limiting](./03-mcp.md#tool-출력-제한)
- [Permission and API Key](./03-mcp.md#권한과-api-key)
- [Human Approval](./03-mcp.md#human-approval)
- [Prompt Injection Defense](./03-mcp.md#prompt-injection-방어)
- [MCP Log Table](./03-mcp.md#mcp-로그-테이블)
- [MCP Python Structure](./03-mcp.md#python-모듈-구조)

### Agent Orchestration

- [Agent Orchestration](./04-agent-orchestration.md)
- [Workflow vs Agent](./04-agent-orchestration.md#workflow와-agent의-차이)
- [Agent State](./04-agent-orchestration.md#agent-state)
- [Direct Agent Loop](./04-agent-orchestration.md#직접-구현하는-agent-loop)
- [Action Schema](./04-agent-orchestration.md#action-종류)
- [Stop Conditions](./04-agent-orchestration.md#stop-conditions)
- [LangGraph](./04-agent-orchestration.md#langgraph를-쓰는-이유)
- [LangGraph Nodes](./04-agent-orchestration.md#langgraph-노드-예시)
- [Multi-Agent](./04-agent-orchestration.md#multi-agent를-언제-나누나)
- [Manager Pattern](./04-agent-orchestration.md#manager-pattern)
- [Handoff Pattern](./04-agent-orchestration.md#handoff-pattern)
- [Agent Policy](./04-agent-orchestration.md#agent-policy)
- [Agent Run Storage](./04-agent-orchestration.md#agent-run-저장)
- [Agent SSE Events](./04-agent-orchestration.md#sse-이벤트)
- [Agent Failure Patterns](./04-agent-orchestration.md#agent-실패-패턴)

### Memory, Evaluation, Observability

- [Memory, Evaluation, Observability](./05-memory-evaluation-observability.md)
- [Short-term Memory](./05-memory-evaluation-observability.md#short-term-memory)
- [Long-term Memory](./05-memory-evaluation-observability.md#long-term-memory)
- [Memory Write Policy](./05-memory-evaluation-observability.md#memory-write-policy)
- [Memory Retrieval](./05-memory-evaluation-observability.md#memory-retrieval)
- [Evaluation](./05-memory-evaluation-observability.md#evaluation)
- [Golden Dataset](./05-memory-evaluation-observability.md#golden-dataset)
- [Observability](./05-memory-evaluation-observability.md#observability)
- [Trace](./05-memory-evaluation-observability.md#trace)
- [Metrics](./05-memory-evaluation-observability.md#metrics)
- [Debug Dashboard](./05-memory-evaluation-observability.md#debug-dashboard)

### Python Architecture

- [Python Architecture](./06-python-architecture.md)
- [Recommended Package Structure](./06-python-architecture.md#recommended-package-structure)
- [OOP Boundary](./06-python-architecture.md#oop-boundary)
- [Domain Model](./06-python-architecture.md#domain-model)
- [Use Case](./06-python-architecture.md#use-case)
- [Repository](./06-python-architecture.md#repository)
- [Unit of Work](./06-python-architecture.md#unit-of-work)
- [Dependency Injection](./06-python-architecture.md#dependency-injection)
- [Error Model](./06-python-architecture.md#error-model)
- [Test Strategy](./06-python-architecture.md#test-strategy)

## 읽는 순서

1. 전체 구조를 잡으려면 [LLM Runtime](./01-llm-runtime.md)을 먼저 본다.
2. 내부 데이터 기반 답변을 만들려면 [RAG](./02-rag.md)를 본다.
3. 외부 API와 도구 연동을 만들려면 [MCP](./03-mcp.md)를 본다.
4. 여러 단계를 자동으로 실행하려면 [Agent Orchestration](./04-agent-orchestration.md)을 본다.
5. 운영 품질을 챙기려면 [Memory, Evaluation, Observability](./05-memory-evaluation-observability.md)를 본다.
6. Python 코드 구조를 정하려면 [Python Architecture](./06-python-architecture.md)를 본다.
