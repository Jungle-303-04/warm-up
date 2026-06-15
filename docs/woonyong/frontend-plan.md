# RepoPilot 프론트엔드 페이지 기획

## 서비스 한 줄 정의

GitHub 저장소를 동기화해 **심볼 단위로 인덱싱(임베딩)** 하고, **하이브리드 검색**으로 근거(citation)
있는 코드 청크를 찾으며, AI가 **직접 write하지 않고 citation+승인이 있는 제안(proposal)만** 만든다.
핵심 가치 = "코드-문서 정합성 검증 + 사람이 승인하는 AI 제안(HITL)".

## 백엔드 능력 ↔ 화면 매핑 (현재 API 기준)

| 백엔드 | 화면에서 쓰는 곳 |
|--------|------------------|
| `POST /pipeline/sync` (enqueue/inline) | 저장소 동기화 트리거 |
| `GET /pipeline/sync/{job_id}` (상태+이벤트) | 동기화 진행/타임라인 |
| `POST /pipeline/search` (벡터+키워드 융합, 점수·citation) | 검색 결과 |
| `POST /pipeline/run` (데모: code_references·chunks·proposals·stages) | 파이프라인/제안 데모 |
| (예정) 제안 승인 API · GitHub OAuth | 제안 검토·로그인 |

---

## 페이지 구성

### 1. 저장소 대시보드 `/repositories`  — ✅ 지금 가능
연결된 저장소 목록 + 새 저장소 연결.
- 카드: 저장소명, 브랜치, 마지막 sync 시각/상태(succeeded/failed/running), 청크 수.
- 액션: **저장소 연결**(GitHub URL + 브랜치 입력 → `POST /pipeline/sync`), **재동기화**.
- 상태: 비어있음(첫 연결 유도), 로딩, 에러.

### 2. 동기화 상세 `/repositories/{id}/sync/{jobId}`  — ✅ 지금 가능
한 sync job의 진행 상황.
- **이벤트 타임라인**(job_queued→started→fetch→diff→files_persisted→chunks_upserted→succeeded).
  `GET /pipeline/sync/{job_id}`를 폴링.
- diff 요약(added/modified/deleted/unchanged 개수), 실패 시 에러 메시지.
- 상태 배지: queued/running/succeeded/failed.

### 3. 검색 `/search`  — ✅ 지금 가능(Postgres 필요)
하이브리드 검색의 핵심 화면.
- 입력: 쿼리, 저장소/브랜치 선택, top-k.
- 결과 카드(각 hit): **코드 스니펫**(심볼명·언어·라인), **citation**(`repo:path:lines@commit`),
  **점수 분해 막대**(final / vector / keyword) — 하이브리드를 눈으로 확인·튜닝.
- 액션: GitHub 원본 라인으로 열기, "이 청크로 제안 만들기".
- 상태: 무결과(쿼리 보정 힌트), PG 미설정 시 503 안내.

### 4. 제안 검토·승인 `/proposals`  — ⏳ 승인 API(Phase B) 필요
제품 차별점. AI 제안을 사람이 승인/반려(HITL).
- 목록: 제안 유형(related-code/stale-link), 대상 경로, **confidence**, 상태(pending/approved/rejected).
- 상세: **근거(evidence) = citation 목록**, 제안 변경 내용(diff 형태), 코드-문서 링크 상태(verified/stale/broken).
- 액션: **승인 / 반려**(결정 시 사유), 승인 시 후속(PR/이슈 코멘트는 Phase D).
- 원칙 노출: "AI는 직접 수정하지 않으며, 승인된 제안만 반영됨"을 UI에 명시.

### 5. 질의응답(RAG Ask) `/ask`  — ⏳ 답변 생성(Phase 2) 필요
- 자연어 질문 → 검색 → **근거 인용이 달린 답변**, 근거 부족 시 "모름" 표시(환각 방지).
- 각 문장에 citation 칩, 출처 패널.

### 6. 설정 `/settings`  — 일부 지금 가능
- 임베딩 제공자/모델/차원, 하이브리드 가중치(vector/keyword), 전문검색 config.
- GitHub 연결(토큰/OAuth, Phase 3), retention 정책.

---

## 공통/횡단 요소

- **CitationChip** 컴포넌트: `path:lines@commit` 표준 표시 + GitHub 딥링크. 검색·제안·답변에서 재사용.
- **CodeSnippet**: 언어 하이라이트 + 라인 강조.
- **JobStatusBadge / EventTimeline**: 동기화·워커 상태.
- **ScoreBar**: 하이브리드 점수 분해.
- 전역: 네비게이션(저장소/검색/제안/설정), 로그인(Phase 3), 로딩/빈/에러 상태, 토스트.

## 구축 우선순위 (백엔드 준비도 기준)

1. **지금 바로**: 저장소 대시보드(1) + 동기화 상세(2) + 검색(3). 현재 API로 완결되는 핵심 루프
   ("연결→동기화→검색")이라 데모 가치가 가장 크다.
2. **Phase B 후**: 제안 검토·승인(4) — 제품 차별점.
3. **Phase 2 후**: RAG Ask(5).
4. **Phase 3 후**: 로그인/권한, 설정의 GitHub 연결.

## 권장 MVP 화면 (데모용)

**검색(3)** 한 화면이 가장 임팩트 크다 — 쿼리 → 하이브리드 결과 + 점수 분해 + citation은
이 서비스의 정체성을 한눈에 보여준다. 여기에 저장소 연결/동기화(1·2)를 붙이면 완결된 데모가 된다.
