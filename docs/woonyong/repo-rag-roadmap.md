# repo-rag 로드맵 (현재 → 실서비스)

## 현재 상태 (구현 완료)

- 심볼 단위 청킹 + 역할 분류(`python_classifier`), Markdown 섹션 청킹
- 임베딩 포트 + OpenAI(배치·재시도) / 결정론적(오프라인) 어댑터
- pgvector 하이브리드 검색(벡터 코사인 + tsvector, 가중합 융합)
- 저장소 두 구현(in-memory / Postgres), active-row 소프트삭제
- 백그라운드 폴링 워커(`FOR UPDATE SKIP LOCKED`) + 실패 감사 분리
- UnitOfWork 트랜잭션 경계, FastAPI Depends 네이티브 DI
- 품질 게이트(ruff lint+format), 오프라인 테스트(69 passed)

즉 **"검색까지의 RAG 파이프라인"** 골격까지 완료.

## 갭 분석 (서비스가 되려면)

- **답변 생성(G)**: context packing → LLM 답변 → citation → groundedness 검증. (지금은 retrieve까지)
- **검색 품질**: rerank, metadata 필터, query rewrite, 평가 하니스(golden set, recall@k/MRR)
- **재임베딩 스킵**: `chunk_hash`로 변경분만 임베딩(현재 미구현, 비용 직결)
- **GitHub 실연동**: OAuth, 토큰 암호화 저장, webhook 증분 sync
- **권한**: retrieval 전 permission 필터, 워크스페이스/레포 가시성
- **제품 차별점**: findings/proposals + approval flow, 링크 상태(verified/stale/broken)
- **운영**: alembic 마이그레이션, 재시도/DLQ, advisory lock, 레이트리밋, 표준 에러
- **관측성**: 메트릭/트레이싱 + citation accuracy 등 도메인 지표
- **배포**: docker-compose(pg+pgvector+redis), CI/CD

## 단계별 계획

### Phase 0 — 정리·품질 게이트 ✅ (완료)
ruff(lint+format), 매퍼 분리, 타입 별칭, active-row 헬퍼, repo_rag/README, 본 로드맵,
docker-compose, pre-commit, CI 스캐폴드.

### Phase 1 — 기반 견고화
alembic 마이그레이션, `chunk_hash` 재임베딩 스킵, 검색 평가 하니스(golden set), pyright strict.

### Phase 2 — 답변 + 검색 품질 (사용자 체감 가치)
context packing → LLM 답변(citation·groundedness·근거부족 시 abstain), rerank + metadata 필터.

### Phase 3 — GitHub 실연동 + 권한
OAuth/토큰 암호화, webhook 증분 sync, retrieval 전 permission 필터.

### Phase 4 — 제품 차별점
findings/proposals 생성 + approval flow, 코드-문서 링크 상태 추적.

### Phase 5 — 운영 성숙
재시도/DLQ, advisory lock, 메트릭/트레이싱/대시보드, 레이트리밋, 워커 다중화.

권장 순서: **0 → 1 → 2**. Phase 2~5는 OpenAI 키·실제 Postgres·GitHub 앱 등 외부 인프라와
제품 결정이 필요하다.

---

## 제품 구현 실행 (2026-06-15~)

미구현 영역(에이전트 제안·승인·워커·GitHub·프론트)을 단계적으로 채우는 실행 트래커.
노션 트래커: "RepoPilot 구현 로드맵 (Phase 1–5)".

**아키텍처 결정**

- AI 오케스트레이션: **LangGraph StateGraph + LCEL**. 도메인은 `LlmProposer` 포트만 소유하고,
  LangGraph/LangChain은 infrastructure 어댑터 안에만 둔다(헥사고날 유지).
- LLM: **제공자 비종속** 인터페이스, OpenAI 우선 연결. 테스트는 `GenericFakeChatModel`로
  그래프를 오프라인 실행(키·네트워크 불필요).
- 커밋: 작업 단위별 최소 커밋, 각 커밋은 테스트 green 유지.

**진행**

- ✅ **Phase A — AI 에이전트 코어 (LangGraph 제안 그래프)** (77 passed / 2 skipped)
  - [x] `chore: LangGraph 의존성을 추가`
  - [x] `feat: 제안 생성용 LLM 포트와 에이전트 연결을 추가` (`LlmProposer`, `ProposalDraft`,
        `AgentProposalService`에 주입 + 휴리스틱 fallback 보존)
  - [x] `feat: LangGraph 제안 그래프 어댑터를 추가` (`LangGraphProposer`, chat model 팩토리,
        Fake ChatModel 오프라인 테스트)
  - [x] `feat: 파이프라인에 LLM 제안 그래프를 배선` (`llm_provider` 설정, 서비스 주입)
- ✅ **Phase B — Approval (HITL 결정, "제안=퀘스트" 상태머신)** (91 passed / 2 skipped)
  - [x] `feat: REJECTED 상태와 파이프라인 collect 공개` (9ff5e26)
  - [x] `feat: 제안 리뷰 도메인(레코드·상태전이·포트)` (977d8e8) — PENDING→APPROVED/REJECTED,
        종료 상태 재결정 차단, 결정 이력(decided_at/reason)
  - [x] `feat: 리뷰 서비스 + in-memory 저장소` (86eb848) — generate(수락)/list/approve/reject
  - [x] `feat: 승인/반려 API + 라우터 마운트` (7689f96) — `POST /pipeline/proposals`,
        `GET /pipeline/proposals[?status=]`, `GET/POST .../{id}/approve|reject`
  - [x] `feat: 제안 SQL 모델·매퍼·저장소` (0964787) + `feat: Postgres 영속화 배선` (f167639) —
        `agent_proposals` 테이블, in-memory/SQL 선택, PG-가드 통합 테스트
  - [ ] (후속) LangGraph `interrupt` 기반 승인 게이팅
- ✅ **Phase C — 백그라운드 워커 실제 처리** (96 passed / 4 skipped)
  - [x] `feat: 워커 추상화 + repo-sync 실폴링 워커` (407c9e6) — `Worker`/`HeartbeatWorker`/
        `SyncPollingWorker`/`build_worker`, repo-sync는 `SyncJobPoller`로 sync 큐 실제 소비
  - [x] `fix: 크래시하던 static-publish 워커 제거` (1125251) — 전용 큐 없는 단계는 placeholder 명시
  - 메모: 인덱싱/제안은 sync 워커 내부 인라인 처리. 단계별 전용 큐는 향후 분리 과제.
- ✅ **Phase D — GitHub App (핵심)** (111 passed / 4 skipped)
  - [x] `feat: 웹훅 서명검증 + 설정` (75b913a) — HMAC-SHA256 상수시간 비교
  - [x] `feat: 웹훅 수신 엔드포인트 + sync 트리거` (5ea17ca) — `POST /github/webhook`,
        push → repo_rag sync(큐잉/인라인)
  - [x] `feat: App JWT(RS256) 인증` (ed5ac01) — 10분 만료 한도 준수
  - [x] `feat: 제안 코멘트 포맷팅 + 발행 서비스` (a36d75b) — `GitHubCommentClient` 포트 + httpx 어댑터
  - [ ] (후속) 설치 토큰 교환(network) 실연동, 승인 시 이슈/PR 자동 게시(이슈 링크 모델 필요)
- ✅ **Phase E — 프론트엔드 API 연동** (tsc --noEmit 통과)
  - [x] `feat: 제안 검토 보드 프론트엔드` (2206785) — `lib/api.ts` 타입 클라이언트,
        `ProposalsBoard`(상태 필터·승인/반려·새로고침), 정적 소개 페이지 교체
