# 프론트엔드 핸드오프 프롬프트 (RepoLM 웹)

> 백엔드+프론트를 함께 맡을 Claude에게 그대로 전달. 백엔드 계약은
> `docs/woonyong/backend-handoff-prompt.md`, 권한/공유 모델은 `docs/woonyong/team-sharing-model.md`.
> 이 두 문서가 프론트가 소비할 **API 계약의 진실 공급원**이다.

---

## 스택 / 실행

- Next.js 15(App Router) · React 19 · TypeScript · **Tailwind v4**(`@theme` 토큰) · zustand · lucide-react ·
  react-markdown(+remark-gfm, rehype-sanitize).
- 패키지 매니저는 **pnpm 전용**. ⚠️ npm 절대 금지(pnpm 워크스페이스 node_modules를 깨뜨림).
  깨졌으면 `CI=1 pnpm install`로 복구. 개발: 루트에서 `pnpm dev`(→ `apps/web`), `http://localhost:3000`.
- API 베이스: `NEXT_PUBLIC_API_URL`(기본 `http://localhost:8000`). 백엔드 CORS는 `WEB_APP_URL` 허용 + credentials.
- 커밋: 한글 Conventional Commits, 작업 단위 최소화.

## 디자인 토큰 (globals.css)

shadcn 스타일 HSL 토큰: `background foreground card primary secondary muted accent destructive border input ring`
(+ `-foreground`). 유틸로만 사용(`bg-card text-muted-foreground` 등).
⚠️ **테마(D2, decisions.md)**: **시스템 다크 기본 + 토글(light/dark/system)**, Tailwind만. 진짜 NotebookLM 다크 톤.
`.dark`/`.light` 토큰 + FOUC 방지 부트스트랩 + 토글을 복구해야 함(이전에 라이트 전용으로 제거됨).
아이콘은 `<Icon name="..." size={n} />` 래퍼(의미 기반 name→lucide 매핑).
⚠️ lucide ^0.460은 **GitHub 브랜드 아이콘이 없다** → GitHub 마크는 `icon.tsx`의 `name="github"` 인라인 SVG로 제공.

## 구조 (apps/web/src)

- `app/`: `page.tsx`(→ `<Workspace/>`), `layout.tsx`, `globals.css`.
- `components/`: `workspace`(3패널 셸) = `top-bar` + `sources-panel` + `center-panel` + `studio-panel`.
  - `center-panel`: 탭 대화/보드/뷰어 → `chat-view` / `board-panel`(칸반·주·캘린더·목록) / `viewer-panel`.
  - 그 외: `source-row`, `proposal-card`, `citation-chip`, `markdown-view`, `auth-menu`, `icon`.
- `hooks/`: `use-me`(현재 GitHub 사용자), `use-proposal-publish`(생성+발행, 멱등 캐시).
- `lib/`: `api.ts`(타입 클라이언트), `store.ts`(zustand `useWorkspace`), `fixtures.ts`(목업 데이터),
  `types.ts`(`Author{login,avatar_url}`·`Member`·`Source`·`BoardTask` 등).

## 지금 동작(실연동)하는 것

- **로그인/사용자**: `auth-menu` → `getMe()`(`GET /auth/me`), 로그인 버튼(`/auth/github/login`).
  (실측 완료: 실제 GitHub OAuth 로그인 → 세션 쿠키 → `/auth/me`가 `{user_id, login}` 반환.)
- **제안 발행**: `proposal-card` → `use-proposal-publish` → `generateProposals`(`POST /pipeline/proposals`)
  + `publishProposal`(`POST /github/proposals/{id}/publish`, 로그인 사용자 OAuth 토큰으로 이슈 코멘트).
- `api.ts` 현재 함수: `loginUrl`, `getMe(signal)`, `generateProposals(repository)`, `publishProposal(id, issue)`.
  모든 요청 `credentials:"include"`(세션 쿠키). 동일 사이트(localhost 다른 포트) + SameSite=Lax라 쿠키 전송됨.

## 지금 목업(fixtures)인 것 — `lib/fixtures.ts`

소스 목록·보드 태스크·스레드·추천질문·스튜디오 타일/메모·대화 예시·인용칩·멤버(현재 사용자 제외).
백엔드 엔드포인트가 나오면 이 fixtures를 API 응답으로 교체한다(= 작업 5).

## 내가(이전 세션) 한 것 요약

- 백엔드: OAuth 로그인/세션JWT/토큰저장, 제안 발행 엔드포인트, CORS, Postgres 영속화 정상화 등(별도).
- 프론트: `api.ts` 클라이언트, `auth-menu`, 제안 발행 연결(이후 사용자가 `use-proposal-publish` 훅으로 정리),
  작성자/멤버 식별 데모(`MEMBERS`, `BoardTask.author`, 보드 아바타, 제안 검토자), `icon`에 GitHub 로고 SVG.
- 설계: `team-sharing-model.md`, `backend-handoff-prompt.md` 작성(사용자가 계약 규약으로 보강).

## 확정 결정 반영 (decisions.md 우선)

- **D1 실서비스 MVP** — 목업은 단계적 제거, 실데이터/권한/영속화 목표.
- **D2 테마**: 시스템 다크 기본 + 토글(위 참고). board-simple 라이트 단독은 폐기.
- **D3/D4 소스**: 레포 + 업로드(md/txt/pdf). "+ 소스 추가" = 레포 연결 / 파일 업로드 2-탭 모달(웹검색 제외).
- **D5 보드**: GitHub 미러 + 로컬 태스크 혼합(`origin` 배지). 로컬만 편집 가능.
- **D6 스튜디오**: UML/ERD/계획 + 보고서/마인드맵(혼합 타일).
- **D7 채팅**: 답변 유형 lookup+locate+summarize 우선(`AgentResponse.kind`로 렌더 분기).
- **D8 planning**: 채팅 `schedule` kind + 보드 액션 양쪽.

## 남은 프론트 작업 (계획, 우선순위)

### F1. GitHub 신원 마감 (즉시, 백엔드 불필요)
- `auth-menu`의 현재 사용자 아이콘 → **실제 GitHub 프로필 사진**:
  `<img src={`https://avatars.githubusercontent.com/u/${me.user_id}`} className="h-[18px] w-[18px] rounded-full" />`.
- repo 소스 아이콘 → GitHub 로고: `fixtures.ts` `SOURCE_KINDS.repo.icon` 을 `"folder_code"` → `"github"`.
- 멤버 아바타: `avatar_url` 있으면 이미지, 없으면 이니셜+색(보드 `MemberAvatar`에 이미 패턴 있음).
  외부 이미지는 plain `<img>` 사용(next/image 쓰려면 next.config remotePatterns 필요).

### F2. 디자인 일관성 (즉시)
- 대화/뷰어가 `max-w-2xl`로 가운데 몰려 양옆 휑함 → 보드처럼 넓게(`max-w-3xl`~`max-w-none`)로 일관화.
- 비활성("준비 중") 컨트롤 다수 → 역할 기반 의미 상태로(아래 F4) 점진 교체.

### F3. 보드 다일(多日) 막대 — "3일짜리는 3일 띠로" (요청됨)
- `BoardTask`에 `start?`(YYYY-MM-DD) 추가, `due`=종료. 범위 `[start ?? due, due]`.
- **주 뷰**: 7열 그리드에 태스크를 시작~종료 **칸 span 막대**로, 겹치면 레인(행) 쌓기(Google Calendar 주뷰).
- **캘린더**: 주 행마다 세그먼트로 잘라 막대(주 경계 분할).
- 칸반/목록은 단일 칩 유지.

### F4. 팀 공유/가시성 UI (team-sharing-model.md 반영)
- 공유 항목에 **작성자 아바타+시간**, 소스/보드 "팀 공유" 배지, 대화 "개인" 잠금 + "팀 공유" 토글.
- 역할별 상태: viewer는 소스연결·발행 버튼 **"권한 없음"**(현재 "준비 중" 자리). owner/member만 활성.
- 보드는 GitHub Issue 미러 톤(라벨·이슈번호·작성자, 로컬편집 UI 없음).

### F5. 목업 → 실데이터 교체 (백엔드 엔드포인트 도착 시; 계약 = backend-handoff-prompt.md)
- 워크스페이스/멤버: `GET /workspaces`, `/workspaces/{id}/members` → TopBar 전환·멤버 표시.
- 소스: `GET /pipeline/repositories` → `sources-panel`. 연결은 `POST /pipeline/sync`(쓰기 역할).
- **대화**: `POST /conversations`·`/messages`(답변 그래프)·`GET /conversations`·`/share` → `chat-view`.
  응답 `citations[]`로 인용칩. `scope_source_ids`로 "N개 소스 기준" 복원.
- **보드 미러**: `GET /board?workspace_id=&label=RepoLM` → `board-panel`(읽기전용, 멀티레포 집계).
- 응답 봉투 `{items, next_cursor}`, author `{login, avatar_url}`, 에러 `{detail, code}` 규약 준수.

### F6. repo 소스 파일 트리 뷰어 (범위 큼)
- `GET /pipeline/repositories/{id}/files`(트리) + `/files/{path}`(본문) → `viewer-panel`에 **폴더 트리 + 파일 렌더**
  (md=마크다운, 코드=읽기전용 하이라이트). "문서만" 필터. 풀 Git 브라우징은 GitHub 링크 위임(IDE 아님).

## 함정 / 주의

- **pnpm만**(npm 금지). 빌드 깨지면 `CI=1 pnpm install`.
- lucide에 GitHub 브랜드 아이콘 없음 → 인라인 SVG(`name="github"`).
- 전 화면이 데모 셸 — `fixtures.ts`가 목업 출처. 실데이터 교체 전까지 "준비 중"/목업 명시 유지.
- 세션 쿠키는 httponly `rp_session`; 프론트는 직접 못 읽고 `credentials:"include"`로만 전송.
- git: 같은 파일 동시 편집 시 `git add -A` 금지(상대 미커밋 변경 휩쓸림). 파일 지정 스테이징.

## 현재 git 상태

- 브랜치 `woonyong`(origin 대비 다수 앞섬, 푸시는 로컬에서 `git push origin woonyong`).
- 백엔드 pytest 128 passed/6 skipped, 프론트 `pnpm --filter @repolm/web typecheck`(tsc) green 기준 유지.

---
