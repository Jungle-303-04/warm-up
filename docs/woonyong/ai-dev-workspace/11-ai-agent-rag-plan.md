# AI Agent와 RAG 계획

## AI 범위

AI는 project knowledge, issue, code를 연결하기 위해 존재한다. 제품 모델과 분리된 범용 chat layer가 되면 안 된다.

이 문서는 AI/RAG의 제품 원칙을 다룬다. Repo RAG 저장소, sync job,
chunk persistence, pgvector 전환 같은 구현 순서는
`16-repo-rag-implementation-plan.md`를 기준으로 한다.

## MVP 기능

1. Citation이 있는 repo-aware Q&A
2. Page 기준 related-code suggestion
3. 낡은 문서-코드 링크 감지
4. 문서 또는 회의록 기반 issue draft 생성
5. PR 요약과 task/document update 제안

## Retrieval Source

- Markdown/MDX pages
- task properties
- meeting notes
- decisions/specs/API docs
- GitHub issues
- GitHub PRs
- code files and symbols
- code-doc links

## Retrieval Pipeline

```text
query
  ↓
intent classification
  ↓
permission filter
  ↓
hybrid search
  ↓
rerank
  ↓
context pack
  ↓
answer/proposal with citations
```

Permission filtering은 retrieval 전에 실행한다.

## Chunking

Docs:

- heading 기준 chunk
- frontmatter 보존
- parent page metadata 유지

Code:

- file과 symbol 기준 chunk
- repo, path, symbol, line range, commit 보존
- generated/secret file 제외

Issues/PRs:

- title/body/comment를 분리해 chunk
- author, date, state, label 보존

## Agent Proposal Schema

```json
{
  "type": "related_code_suggestion",
  "target_id": "item_123",
  "summary": "Auth 구현 관련 코드 링크 제안",
  "evidence": [],
  "changes": [],
  "confidence": 0.82,
  "status": "pending"
}
```

## 출력 규칙

- source를 인용한다.
- 불확실성을 표시한다.
- direct write보다 proposal을 우선한다.
- 사실과 추론을 구분한다.
- state change에는 human approval step을 둔다.

## MCP와 LangChain

MVP core behavior는 MCP나 LangChain에 의존하지 않는다.

추천:

- internal tool을 먼저 구현한다.
- tool contract를 깔끔하게 유지한다.
- 외부 agent 접근이 필요해지면 MCP server를 추가한다.
- LangChain은 orchestration 복잡도를 줄일 때만 사용한다.

Internal tools:

- `search_docs`
- `search_code`
- `get_item`
- `get_issue`
- `propose_issue`
- `propose_doc_patch`
- `propose_code_link`
- `check_code_link_status`

## 평가 지표

추적할 것:

- citation accuracy
- permission leak rate
- accepted proposal rate
- stale-link detection precision
- issue/doc 생성 시간 절감
- AI proposal 이후 사용자 수정량
