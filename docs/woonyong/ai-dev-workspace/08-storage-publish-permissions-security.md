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

MVP는 GitHub OAuth 로그인으로 시작한다. 사용자는 GitHub에서 권한을 승인하고, RepoPilot은 GitHub access token으로 사용자가 접근 가능한 repo 목록과 repo content, issue, PR을 읽는다.

브라우저 로그인 유지는 RepoPilot 자체 session cookie로 처리한다.

```text
GitHub OAuth access token
-> GitHub API 호출용
-> backend에 암호화 저장
-> browser에 직접 노출하지 않음

RepoPilot session cookie
-> RepoPilot 로그인 유지용
-> HttpOnly Secure SameSite cookie
-> sessions table에서 revoke/expire 관리
```

JWT는 P0 기본값으로 쓰지 않는다. 초기 web app은 server-side session이 logout, revoke, 권한 갱신 반영에 더 단순하다.

GitHub OAuth scope는 최소로 시작하되 private repo 분석이 필요하면 `repo` scope가 필요할 수 있다. OAuth 토큰은 사용자의 GitHub 권한 범위 안에서만 동작한다.

GitHub App permission은 P1에서 repo 설치, webhook, 조직 운영을 강화할 때 추가한다. 권한은 좁게 시작한다.

- repository metadata: read
- contents: read
- issues: read/write
- pull requests: read
- members/permissions: 가능한 경우 read
- webhooks: read events

Write action은 명시적 사용자 승인이 필요하다.

## GitHub 권한 상태

RepoPilot은 repo sync 전과 주기적 background check에서 GitHub 권한 상태를 확인한다.

확인할 것:

- OAuth token 유효성
- 필요한 scope 보유 여부
- 사용자의 repo 접근 권한
- 조직 SSO 승인 필요 여부
- repo 삭제, 이전, rename 여부
- GitHub API rate limit

권한 상태는 `RepositoryConnection`에 저장한다.

```text
permission_status:
ok
needs_reauth
insufficient_scope
sso_required
repo_access_lost
rate_limited

required_action:
none
reconnect_github
grant_scope
authorize_sso
request_repo_access
wait_for_rate_limit
disconnect_repo
```

사용자 안내 예시:

- `needs_reauth`: GitHub 연결이 만료되었습니다. 다시 로그인해 주세요.
- `insufficient_scope`: 이 private repo를 분석하려면 추가 GitHub 권한이 필요합니다.
- `sso_required`: 조직 SSO 승인이 필요합니다.
- `repo_access_lost`: 이 repo에 대한 GitHub 접근 권한이 없어 sync가 중지되었습니다.
- `rate_limited`: GitHub API 사용량 제한에 도달했습니다. 다음 재시도 시각 이후 자동 재개합니다.

권한 문제가 있으면 sync job은 실패보다 `blocked` 또는 `skipped` 상태로 남기고, 관련 proposal과 automation은 `needs_review` 또는 `blocked`로 전환한다.

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
- GitHub access token은 browser에 전달하지 않는다.
- session cookie는 `HttpOnly`, `Secure`, `SameSite=Lax` 이상으로 설정한다.
- logout과 token revoke는 server-side session과 GitHub account record에서 처리한다.
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
