# 제품 요구사항

## 기준 문서

제품 방향은 [00. 제품 기획서](./00-product-plan.md)를 기준으로 한다. 이 문서는 그 방향을 구현 가능한 요구사항으로 풀어쓴다.

## MVP 사용자 흐름

1. 사용자가 GitHub OAuth로 로그인한다.
2. 접근 가능한 repo 목록에서 분석할 repo를 선택한다.
3. RepoPilot이 default branch, open PR branch, 최근 active branch를 자동 sync한다.
4. RepoPilot이 repo 파일, 문서, 이슈, PR, commit, label, milestone을 인덱싱한다.
5. RepoPilot이 문서-코드 연결 후보, 작업 영역, stale 문서, missing evidence를 자동 생성한다.
6. 사용자는 대시보드에서 finding과 proposal을 확인한다.
7. 사용자는 GitHub issue 생성/상태 변경, 문서 수정, comment 작성 proposal을 승인하거나 보류한다.
8. RepoPilot은 승인된 action을 GitHub나 문서에 반영한 뒤 다시 sync해 결과를 검증한다.

## 기능 요구사항

### repo 연결

- 사용자는 GitHub OAuth로 로그인하고 접근 가능한 repo를 선택할 수 있다.
- 선택된 repo는 `RepositoryConnection`으로 저장된다.
- 기본 분석 대상은 default branch, open PR branch, 최근 active branch다.
- repo indexing은 file path, symbol, commit SHA, issue, PR, commit metadata를 저장한다.
- repo 연결 해제 시 내부 source, chunk, embedding, finding, proposal은 검색에서 즉시 제외되고 cleanup 대상이 된다.

### 페이지와 아이템

- 사용자는 트리 형태로 페이지를 생성할 수 있다.
- 모든 페이지는 `WorkspaceItem`으로 저장된다.
- MVP 타입은 `wiki`, `task`, `meeting`, `decision`, `spec`, `api_doc`, `schedule`, `milestone`이다.
- 각 아이템은 status, assignee, due date, start/end, tags, GitHub issue, related code, visibility, publish state를 가질 수 있다.
- 모든 아이템은 Markdown/MDX export가 가능해야 한다.

### 뷰

- Table view는 공통 속성으로 아이템을 정렬하고 필터링한다.
- Kanban view는 `status` 기준으로 아이템을 그룹화한다.
- Calendar view는 `start`, `end`, `due`를 사용한다.
- 정적 viewer는 읽기 전용 뷰와 필터를 제공한다.

### GitHub

- RepoPilot은 GitHub issue를 가져와 repo 기준 작업 view로 보여줄 수 있다.
- RepoPilot은 missing evidence나 stale 문서를 근거로 GitHub issue draft를 만들 수 있다.
- GitHub write action은 사용자 승인 이후에만 실행된다.
- repo-specific data를 보여주기 전 GitHub permission check가 적용되어야 한다.

### 코드-문서 링크

- 사용자는 문서에 code reference를 수동으로 붙일 수 있다.
- AI는 code reference를 추천할 수 있지만, 승인 전까지는 suggested 상태다.
- code reference는 file path, line range, symbol, commit, GitHub URL을 가질 수 있다.
- link status는 verified, stale, broken, suggested, none으로 표시된다.
- 링크 클릭 시 로컬 경로가 있으면 VS Code를 열고, 없으면 GitHub로 이동한다.

### AI

- AI는 프로젝트 문서, 이슈, 코드 chunk를 근거로 질문에 답할 수 있다.
- AI는 페이지와 관련된 코드를 추천할 수 있다.
- AI는 repo 변경 이후 stale code-doc link를 감지할 수 있다.
- AI는 issue draft와 document update proposal을 만들 수 있다.
- AI 출력은 citation/evidence와 confidence를 포함해야 한다.

### 퍼블리싱

- 사용자는 선택한 페이지와 뷰를 정적 사이트로 퍼블리싱할 수 있다.
- 공개 viewer는 편집할 수 없다.
- 퍼블리싱 결과물은 page tree, search index, filter, code-link status를 포함한다.
- private 또는 권한 제한 데이터는 퍼블리싱되지 않아야 한다.

## 비기능 요구사항

- 정적 페이지는 앱 서버 없이 빠르게 읽혀야 한다.
- indexing job은 request/response 경로 밖에서 실행되어야 한다.
- 모든 GitHub write action은 audit 가능해야 한다.
- secret과 환경 파일은 indexing과 publishing에서 제외해야 한다.
- permission filter는 retrieval과 AI generation 전에 적용되어야 한다.
- 사용자가 lock-in을 느끼지 않도록 Markdown/MDX export를 제공해야 한다.

## MVP 인수 기준

1. GitHub OAuth 로그인 후 repo 목록을 볼 수 있다.
2. 사용자가 repo를 선택하면 자동 sync job이 생성된다.
3. branch, docs, code, issues, PRs, commits가 repo 기준으로 인덱싱된다.
4. finding dashboard가 stale document, partial feature, missing test를 보여준다.
5. AI가 repo-aware 질문에 citation과 함께 답할 수 있다.
6. AI는 GitHub/document update를 직접 적용하지 않고 proposal로만 만든다.
7. 승인된 proposal은 GitHub API나 문서 patch로 실행되고 재-sync로 검증된다.

## MVP 제외 범위

- 완전한 Notion식 database builder
- GitHub Projects v2 전체 복제
- 완성형 VS Code extension
- Google Docs 수준의 multi-cursor editor
- 자동 code write 또는 merge
- public viewer의 write action
