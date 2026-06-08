# 저장소, 퍼블리싱, 권한, 보안

## 저장소 계약

RepoPilot은 책임별로 저장소를 나눈다.

```text
PostgreSQL
실시간 app data, item, view, permission, proposal

pgvector
retrieval index

Redis
queue/cache/presence support

GitHub
code, issue, PR, repo permission

Static output
published viewer artifact
```

Markdown/MDX export는 장기 보관 포맷이다. 하지만 실시간 편집 state는 app DB/CRDT layer에 둔다.

## Publish 모델

Publishing은 snapshot을 만든다.

```text
Draft item
        ↓
publish eligibility check
        ↓
static render
        ↓
search/filter index
        ↓
deploy artifact
```

정적 viewer는 기본 읽기 기능에 app API 인증을 요구하지 않아야 한다.

## Publish 가능 여부

Publish 가능:

- public wiki/spec/decision page
- public meeting summary
- 읽기 전용 task/calendar/kanban view
- 승인된 code link

Publish 불가:

- private page
- 승인되지 않은 AI proposal
- private GitHub issue content
- secret 또는 environment file
- 명시적으로 허용되지 않은 private repo code snippet

## 권한 모델

실제 권한은 다음의 교집합이다.

1. Workspace role
2. Project role
3. GitHub repo permission
4. Item visibility
5. Publish visibility

Workspace role:

- owner
- admin
- editor
- viewer

Public anonymous user는 항상 read-only이며, published content만 볼 수 있다.

## GitHub Access

GitHub App permission은 좁게 시작한다.

- repository metadata: read
- contents: read
- issues: read/write
- pull requests: read
- members/permissions: 가능한 경우 read
- webhooks: read events

Write action은 명시적 사용자 승인이 필요하다.

## 초대와 접근 정책

App membership과 GitHub repository access는 다르다.

Invite state:

```text
invited
pending_app_signup
pending_github_access
active
limited
revoked
```

사용자가 RepoPilot에 초대되었지만 GitHub repo access가 없으면 repo-aware docs, issues, code search, RAG context를 잠근다.

## RAG 권한 규칙

Retrieval은 model이 context를 보기 전에 source를 permission filter해야 한다.

먼저 retrieval한 뒤 generation 후 숨기는 방식은 금지한다. Permission filtering은 vector search, keyword search, reranking, context-pack construction 전에 적용한다.

## 보안 규칙

- `.env`, secret file, private key, credential, generated artifact는 indexing에서 제외한다.
- GitHub token은 암호화 저장한다.
- 승인된 agent action에는 audit log를 남긴다.
- AI가 사용자 권한을 우회하지 못하게 한다.
- Static export는 rendering 전에 visibility check를 실행한다.
- private repo code link는 명시적 설정 없이는 public output에 나오지 않는다.

## Audit Event

기록할 것:

- GitHub App installation
- repo connection
- permission change
- publish event
- AI proposal approval/rejection
- issue write action
- code-doc link approval
- stale detection update
