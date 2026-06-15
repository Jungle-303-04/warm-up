# warm-up woohyun 브랜치 구현 분석

## 최신 상태

- 저장소: `Jungle-303-04/warm-up`
- 브랜치: `origin/woohyun`
- 최신 확인 HEAD: `070d2b4f03596efada8b9c81aebefd311f2062db`
- 최신 커밋: `Add GitHub dashboard integration`
- 작성자: `woohyun <haeli0312@gmail.com>`
- 작성 시각: `2026-06-12T00:39:13+09:00`
- 확인 시각: `2026-06-12 13:23:20 +0900`

현재 우현 브랜치는 AI 요약 서비스의 완성형이라기보다, AI가 읽을 재료를 모으기 위한 협업 게시판의 첫 세로 흐름이다. 게시글, 댓글, 태그, 인증, Notion 문서 조회, GitHub Issue/PR/commit 조회가 같은 화면 구조 안에 들어왔다.

## 다른 담당자 문서에서 가져온 운영 방식

- 민정 문서에서 배운 점: 최신 확인 커밋과 실제 구현 여부를 분리한다. 라우터, 서비스, 저장소가 있어도 실제 DB insert가 없으면 stub이라고 적는다.
- 찬빈 문서에서 배운 점: 동작하는 세로 흐름을 뚫은 것은 인정하되, 본인이 설명할 수 있는 코드 소유권과 검증 루프를 다음 관찰 지점으로 둔다.
- 가인 문서에서 배운 점: 첫 커밋부터 구현 의도가 어떻게 바뀌었는지 보고, 요청/응답 스키마, 404, 재현성, N+1, 실행 문서를 위험 포인트로 본다.

## 현재 작업 형식

우현은 기능을 얇게 쪼개기보다 한 번에 제품 흐름을 세로로 밀었다.

1. 프로젝트 문제와 범위를 긴 기획서로 먼저 잡았다.
2. FastAPI와 React를 붙이고 PostgreSQL SQL 파일을 추가했다.
3. 게시글 CRUD를 작업 로그 도메인으로 정의했다.
4. JWT 인증, 작성자 권한, 댓글, 태그, 검색, 페이징을 한 커밋에 함께 넣었다.
5. Notion 문서 조회를 붙인 뒤, 다음 커밋에서 GitHub 대시보드 조회를 추가했다.

## 구현한 것

- 백엔드
  - `FastAPI` 단일 앱 `backend/app/main.py`
  - `psycopg` 직접 SQL 실행
  - `/health`, `/db-health`
  - `/auth/signup`, `/auth/login`, `/auth/me`
  - `/posts` 목록, 생성, 상세, 수정, 삭제
  - `/comments/post/{post_id}`, `/comments/{comment_id}`
  - `/integrations/notion/docs`, `/integrations/notion/docs/{page_id}`
  - `/integrations/github/issues`, `/pulls`, `/commits`
- 데이터베이스
  - `posts`, `users`, `comments`, `tags`, `post_tags`
  - `posts.user_id`, `comments.user_id` 외래 키
  - 태그 중복 방지와 post-tag 연결 테이블
- 프론트엔드
  - React Router 기반 페이지 라우팅
  - 게시글 목록/상세/작성/수정
  - 로그인/회원가입
  - 댓글 작성/수정/삭제 UI
  - Notion 문서 목록/상세 화면
  - GitHub Issue/PR/commit 대시보드

## 의미 있는 커밋 단위 분석

### 1. 공통 문서 기반: `7fd8b07` -> `be69559`

우현 작업 이전에 저장소에는 README, 풀스택 기술 로드맵, AI 구현 구조, AI 개발 워크스페이스 문서가 들어와 있었다. 이 구간은 우현의 직접 구현이라기보다 브랜치가 물려받은 공통 학습/기획 기반이다.

- 하고 있던 것: 기술 선택, 프론트/백엔드/데이터 계층, RAG/MCP/Agent 같은 AI 응용 키워드를 정리했다.
- 의도: 팀 프로젝트를 그냥 CRUD 과제로 보지 않고, AI 개발 도구와 협업 보드로 확장할 언어를 미리 맞추려는 기반이다.
- 고려하지 못한 것: 우현 브랜치 구현과 직접 연결되는 실행 절차, 환경 변수, 최소 API 계약은 아직 없다.
- 어떻게 고치나: 우현 분석 문서에서는 이 구간을 구현 커밋으로 보지 않고, 이후 기획과 코드가 기대는 공통 배경으로만 연결한다.

### 2. 최초 제품 기획: `4d662be`

`docs/AI_Team_Sync_Board_Project_Plan.md`가 처음 추가됐다. Notion, GitHub, 게시판, AI Agent의 역할을 나누고, 팀원이 오늘 할 일과 진행 상황을 확인하는 서비스를 목표로 잡았다.

- 하고 있던 것: 제품의 문제, 도구별 역할, 사용자 시나리오, 요구사항, 기술 스택, 로드맵을 한 문서에 담았다.
- 의도: 구현 전에 "게시판 CRUD가 왜 필요한가"를 AI 브리핑의 입력 데이터로 설명하려 했다.
- 고려하지 못한 것: 범위가 넓다. 게시판 CRUD, 인증, 댓글, 태그, Notion, GitHub, RAG, MCP, Agent를 모두 열어 두어 첫 구현 단위가 흐려질 수 있다.
- 어떻게 고치나: MVP는 "로그인한 사용자가 작업 로그를 쓰고, GitHub/Notion 데이터를 읽어 대시보드에서 보는 것"으로 자르고, AI 요약은 그 다음 단계로 둔다.

### 3. 기획서 재정리: `eed5fb5`

기획서가 서비스 문서 형태로 다시 정리됐다. 문제 정의 표, 기능 목표, 사용자 니즈, 시나리오, 필수/추천/제외 범위가 더 명확해졌다.

- 하고 있던 것: 초안의 긴 설명을 제품 문서 구조로 재배열했다.
- 의도: 개인 과제 기획 공유와 구현 범위 합의를 위해 읽히는 문서로 다듬으려 했다.
- 고려하지 못한 것: "필수 구현"이 여전히 많다. RAG, MCP, Agent까지 필수처럼 보이면 실제 CRUD 안정화보다 데모 범위가 커질 수 있다.
- 어떻게 고치나: 문서 하단에 현재 구현 상태표를 추가해 `완료`, `진행 중`, `미구현`, `보류`를 분리한다.

### 4. 첫 작동 세로 흐름: `a0d1c52`

45개 파일이 한 번에 추가됐다. 이 커밋이 우현 브랜치의 실질적 핵심이다.

- 하고 있던 것: FastAPI 백엔드, PostgreSQL SQL 파일, React 프론트, JWT 인증, 게시글 CRUD, 댓글, 태그, 검색, 페이징, Notion 조회를 한 번에 넣었다.
- 의도: 계획서의 "작업 로그 게시판 + 외부 문서 조회"를 실제 화면으로 만져볼 수 있게 만드는 것이다.
- 잘한 점:
  - `PostCreate`, `PostUpdate`, `PostRead`, `PostListResponse`로 요청/응답 스키마를 분리했다.
  - 게시글 type/status/priority를 `Literal`로 제한했다.
  - 생성, 수정, 삭제는 로그인 사용자 기준으로 처리했다.
  - 수정/삭제에서 작성자 권한을 확인한다.
  - 태그를 별도 테이블로 정규화하고 중복 입력을 정리한다.
  - 목록은 검색, type, status, tag 필터와 페이징을 지원한다.
  - Notion API 오류와 설정 오류를 별도 예외로 나눴다.
- 고려하지 못했거나 위험한 점:
  - `backend/requirements.txt`가 UTF-16 LE로 저장되어 있다. `pip install -r` 재현성이 깨질 수 있다.
  - 백엔드 핵심 로직이 `main.py` 800줄 이상에 몰려 있다.
  - SQL 파일은 있지만 적용 순서, 실행 명령, `.env.example`이 없다.
  - `JWT_SECRET_KEY`, `DATABASE_URL`, Notion 설정이 없으면 import/startup 단계에서 바로 막힌다.
  - 목록/상세 조회는 공개이고 생성/수정/삭제만 인증이다. 팀 전체 공개 정책인지, 내 글만 보기 정책인지 결정이 필요하다.
  - 프론트 API base URL이 여러 파일에 `http://127.0.0.1:8000`으로 중복된다.
  - 프론트 README가 Vite 기본 템플릿 그대로라 실행 절차가 프로젝트와 맞지 않는다.
  - 테스트와 smoke 검증 결과가 없다.
- 어떻게 고치나:
  - `requirements.txt`를 UTF-8로 변환한다.
  - `.env.example`, DB SQL 적용 명령, 백엔드/프론트 실행 순서를 README에 쓴다.
  - `auth`, `posts`, `comments`, `integrations` 라우터로 `main.py`를 나눈다.
  - 최소 smoke 테스트를 만든다: signup -> login -> create post -> list -> detail -> comment.
  - 게시글 공개 범위를 "팀 전체" 또는 "내 글" 중 하나로 문서화한다.

### 5. GitHub 대시보드 통합: `070d2b4`

GitHub Issue, Pull Request, commit 조회 API와 프론트 대시보드가 추가됐다.

- 하고 있던 것: GitHub REST API를 감싸는 서비스와 라우터를 만들고, `/dashboard`에서 open issue, open PR, recent commits를 보여준다.
- 의도: 기획서의 GitHub 진행 상황 확인 기능을 AI 요약 전 단계의 데이터 조회 화면으로 구현하려 했다.
- 잘한 점:
  - GitHub Issues API가 PR도 issue로 반환하는 점을 알고 `pull_request` 항목을 제외했다.
  - rate limit 403일 때 남은 요청 수와 reset 정보를 메시지에 반영하려 했다.
  - token이 없으면 비인증 공개 요청으로도 동작하게 했다.
  - 프론트에서 issue, PR, commit을 병렬로 불러온다.
- 고려하지 못했거나 위험한 점:
  - GitHub/Notion 통합 API가 로그인 없이 열려 있다. 내부 도구라면 괜찮지만 정책을 명시해야 한다.
  - `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN` 설정 예시가 없다.
  - 모든 섹션이 하나의 `isLoading`, `error`를 공유해 한 API 실패가 대시보드 전체 실패처럼 보인다.
  - GitHub 데이터를 게시글/사용자와 연결하지는 않는다. 아직 "보여주기" 단계다.
  - AI 요약, RAG, MCP는 여전히 구현되지 않았다.
- 어떻게 고치나:
  - `.env.example`에 GitHub/Notion 설정을 추가한다.
  - 대시보드 섹션별 loading/error를 분리한다.
  - `auth/me.github_username`과 issue assignee 필터를 연결한다.
  - API 응답을 캐시하거나 rate limit 안내 UI를 둔다.
  - 다음 단계에서 GitHub 데이터와 게시글 작업 로그를 합쳐 요약할 수 있는 내부 DTO를 만든다.

## 고려한 것으로 보이는 것

- 게시판은 단순 글 목록이 아니라 AI가 읽을 작업 로그 저장소라고 봤다.
- Notion은 공식 문서, GitHub는 개발 진행, 게시판은 매일의 맥락이라는 역할 분리를 유지했다.
- 인증은 최소 JWT로 붙이고, 글과 댓글의 수정/삭제 권한은 작성자 기준으로 막으려 했다.
- tags는 문자열 컬럼 하나가 아니라 `tags`, `post_tags`로 분리했다.
- 외부 API 연동은 백엔드에서 감싸 프론트가 직접 토큰을 들고 가지 않도록 했다.
- 처음부터 AI를 붙이기보다, AI가 읽을 데이터 소스를 먼저 화면으로 확인하려 했다.

## 잘한 점

- 제품 의도와 구현이 비교적 잘 이어진다. 기획서의 Notion/GitHub/게시판 역할이 실제 화면과 API로 연결됐다.
- 게시글 CRUD만이 아니라 댓글, 태그, 검색, 페이징까지 협업 게시판의 기본 사용성을 챙겼다.
- Pydantic 스키마를 별도로 둔 점은 가인 브랜치에서 지적된 "DB 모델과 요청 모델 분리" 문제를 피한 좋은 선택이다.
- 권한 검사를 update/delete에 넣은 점은 초반 구현치고 좋다.
- Notion과 GitHub 연동을 서비스 모듈로 분리한 점은 `main.py`가 커져도 외부 API 책임을 나누려는 신호다.

## 못했거나 위험한 점

- `requirements.txt` 인코딩이 UTF-16 LE다. 이건 가장 먼저 고쳐야 하는 재현성 문제다.
- 구현 커밋이 너무 커서 리뷰와 롤백이 어렵다.
- `main.py`가 인증, 게시글, 댓글, 태그 헬퍼, DB 연결을 모두 가진다.
- DB 마이그레이션은 수동 SQL 파일만 있고 적용 방법이 없다.
- 환경 변수 목록과 예시가 없다.
- API 검증은 있지만 DB check constraint가 없어 SQL 직접 입력이나 다른 경로의 오염을 막지 못한다.
- 프론트는 기능 확인용 inline style 중심이고, 로그인 만료나 403 권한 실패 UX가 약하다.
- 외부 통합 API에 인증/권한 정책이 없다.
- 현재는 대시보드 "조회"까지이며 AI 브리핑, RAG, MCP 실행은 아직 없다.

## 개선 우선순위

1. 재현성부터 고친다.
   - `backend/requirements.txt`를 UTF-8로 변환한다.
   - `.env.example`을 추가한다.
   - SQL 적용 순서와 실행 명령을 README에 쓴다.
2. 최소 검증을 추가한다.
   - 백엔드 smoke: 회원가입, 로그인, 게시글 생성, 목록, 상세, 댓글 작성.
   - 프론트 `npm run build`.
3. 코드를 나눈다.
   - `main.py`에서 auth/posts/comments 라우터를 분리한다.
   - DB connection helper를 만든다.
4. 권한 정책을 정한다.
   - 목록/상세는 팀 전체 공개인지 내 글만 공개인지 정한다.
   - Notion/GitHub 통합 API도 로그인 필요 여부를 정한다.
5. GitHub 대시보드를 개인화한다.
   - 현재 사용자 `github_username`으로 assignee 필터를 기본 적용할 수 있게 한다.
6. AI 전 단계 DTO를 만든다.
   - 게시글, 댓글, GitHub issue/PR/commit, Notion 문서 요약 입력을 하나의 briefing context로 묶는다.

## 사용자가 도울 수 있는 행동

우현에게는 다음처럼 말하면 좋다.

```text
방향은 좋다. Notion, GitHub, 게시판을 한 화면으로 가져온 건 기획과 맞다.
다음은 기능을 더 늘리기보다 실행 재현성을 먼저 잠그자.
requirements 인코딩, .env.example, SQL 적용 방법, 최소 smoke 테스트를 정리하고,
그 다음 main.py를 auth/posts/comments/integrations 라우터로 나누자.
AI 요약은 그 뒤에 붙여도 늦지 않다.
```

확정해주면 좋은 제품 결정은 세 가지다.

- 게시글 목록/상세는 팀 전체 공개인가, 작성자 개인 범위인가?
- Notion/GitHub 대시보드는 로그인 사용자만 볼 수 있어야 하는가?
- AI 요약의 첫 입력은 "내 GitHub username + 내 게시글"인가, "팀 전체 데이터"인가?

## 근거 링크

- 최신 HEAD: https://github.com/Jungle-303-04/warm-up/commit/070d2b4f03596efada8b9c81aebefd311f2062db
- 첫 작동 세로 흐름: https://github.com/Jungle-303-04/warm-up/commit/a0d1c52b85c19c1963c63b81fc5b71d446c9c7cb
- 기획서 재정리: https://github.com/Jungle-303-04/warm-up/commit/eed5fb5e341b08b19f3b58f82864748f682fdac8
- 최초 우현 기획: https://github.com/Jungle-303-04/warm-up/commit/4d662be2c485965f0c57a115eb2e6d32c007d344
