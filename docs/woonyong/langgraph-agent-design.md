# RepoLM 에이전트 그래프 설계 (LangGraph)

질문 "유형"마다 다른 처리 경로를 타되, **하나의 그래프**가 분류→라우팅→처리→정리(citation/groundedness)
까지 담당한다. 현재는 제안 생성 그래프(`gather_evidence→draft`) 하나뿐이라, 일반 Q&A·요약·위치찾기·
일정 등 **다양한 답변 유형이 불가능**하다. 이 문서가 그 확장 설계다.

## 원칙 (기존 코드 스타일 유지)

- 헥사고날: 도메인은 포트 `AnswerAgent`(단일 진입)만 소유. LangGraph/LangChain은 infrastructure에만.
- 제공자 비종속: `build_chat_model`(openai 우선). `llm_provider="none"`이면 노드별 휴리스틱 fallback로
  **오프라인 동작**(테스트는 `GenericFakeChatModel`).
- 응답은 **판별 유니온(discriminated union)** — 프론트가 kind로 렌더를 분기(텍스트/제안카드/파일목록/일정).
- 스코프·권한은 그래프 진입 전 주입(선택 소스 = `scope_source_ids`, GitHub 가시성 필터).

## 1. 질문 의도(Intent) = 답변 유형

| intent | 예시 | 처리 경로 | 응답 kind | 지금 가능 |
|---|---|---|---|---|
| `lookup` | "인증 흐름 어떻게 돼?" | retrieve→pack→answer→ground | `answer`(+citations) | 검색까지 O, 답변 X |
| `locate` | "JWT 검증 함수 어디 있어?" | symbol/keyword retrieve | `references`(file:line) | 부분 O |
| `summarize` | "이 저장소 요약해줘" | scope 문서 gather→map-reduce | `summary` | X |
| `consistency` | "문서랑 코드 어긋난 데?" | retrieve(code+doc)→compare→draft | `proposals` | O(제안 그래프 재사용) |
| `howto` | "이 기능 어떻게 구현?" | retrieve→generate(가이드) | `answer` | X |
| `planning` | "이 제안들 일정 잡아줘" | board+approved 제안 로드→schedule | `schedule`(task draft) | X |
| `change` | "최근 바뀐 핵심 로직?" | git 메타 필요 → 없으면 abstain | `abstain`+GitHub 링크 | X(커밋 인덱스 없음) |
| `clarify` / `out_of_scope` | 모호/범위 밖 | 되묻기 또는 정중 거절 | `clarify` | X |

> 의도 분류는 **구조화 출력 LLM**(few-shot) + **키워드 휴리스틱 fallback**. 모호하면 `clarify`로.

## 2. 그래프 구조 (라우터 패턴)

```
START
  → classify_intent
  → (conditional route by intent)
       ├ lookup/howto → retrieve → pack_context → answer → groundedness ┐
       ├ locate       → retrieve(symbol)        → format_references     │
       ├ summarize    → gather_scope            → summarize             │
       ├ consistency  → retrieve(code+doc)       → compare → draft_proposals (→ HITL interrupt)
       ├ planning     → load_board+proposals     → draft_schedule       │
       ├ change       → check_git_meta           → abstain_or_route     │
       └ clarify      → ask_clarify                                     │
  → finalize(citation 결합·confidence·응답 조립) ←──────────────────────┘
  → END
```

- `retrieve / groundedness / finalize`는 **공유 노드**. 핸들러별 subgraph로 분리해 단위 테스트.
- 분기는 LangGraph `add_conditional_edges`(또는 `Command(goto=...)`). 인텐트 추가 = 노드+엣지 한 줄.

## 3. 상태 (AgentState)

```python
class AgentState(TypedDict):
    # 입력
    query: str
    history: Annotated[list[Turn], add]      # 누적 reducer
    scope_source_ids: list[str]
    # 라우팅
    intent: Intent
    route_reason: str
    # 검색/근거
    hits: list[SearchHit]
    context: str
    citations: list[Citation]                # {index, source_id, path, line}
    # 산출(핸들러별 — 하나만 채워짐)
    answer_text: str | None
    references: list[CodeReference]
    summary: str | None
    proposal_drafts: list[ProposalDraft]
    schedule_drafts: list[TaskDraft]
    # 메타
    groundedness: float
    confidence: float
    response: AgentResponse | None           # finalize가 조립
    errors: list[str]
```

## 4. 응답 계약 (프론트 렌더 매핑)

```python
class AgentResponse(BaseModel):
    kind: Literal["answer","references","summary","proposals","schedule","abstain","clarify"]
    text: str | None = None
    citations: list[Citation] = []
    references: list[CodeReference] = []
    proposals: list[ProposalDraft] = []
    schedule: list[TaskDraft] = []
    confidence: float | None = None
```

프론트 채팅은 `kind`로 분기 렌더: `answer`=본문+인용칩, `references`=파일:라인 리스트(클릭→뷰어),
`proposals`=제안카드(승인/반려), `schedule`=보드 추가 미리보기, `abstain`=근거부족+GitHub 위임, `clarify`=되묻기.

## 5. HITL (제안 승인 게이트)

`consistency` 경로의 `draft_proposals` 다음에 LangGraph `interrupt()`로 **사람 승인 대기**.
프론트의 승인/반려가 그래프를 재개(resume)한다. (현재는 그래프 밖 상태머신 — 이 설계로 그래프 내부 일원화)

## 6. 가드레일 / 권한 / 스코프

- 진입 시 `scope_source_ids`로 retrieve 필터. 비면 "소스를 선택하세요" `clarify`.
- 권한: 호출 전 `accessible_repos` 교집합으로 소스 제한(team-sharing-model 2축).
- `groundedness` 임계 미만이면 강제 `abstain`(환각 방지). 각 LLM 노드는 tenacity 재시도.

## 7. 포트 & 배선 (헥사고날)

- 도메인 포트: `AnswerAgent.run(query, scope, history) -> AgentResponse`.
  보조 포트 재사용: `RepoRagRetriever`(검색), `LlmProposer`(제안), 신규 `BoardReader`(planning).
- infra: `LangGraphAnswerAgent`(이 그래프). `dependencies.py`가 `llm_provider`로
  실제/fallback 선택. `POST /conversations/{id}/messages`가 이 포트를 호출(핸드오프 작업 3.5).

## 8. 오프라인 테스트

- 인텐트 분류: 키워드 케이스 + Fake LLM 라우팅 테스트.
- 핸들러별 subgraph 단위 테스트(검색 결과 fixture 주입).
- `llm_provider="none"` 전 경로 그린(네트워크/키 불필요).

## 9. 단계별 구현

1. `AgentState`/`AgentResponse`/`Intent` 정의 + `AnswerAgent` 포트.
2. `classify_intent` + 라우터 + `lookup`(retrieve→pack→answer→ground) — 채팅 핵심.
3. `locate`/`summarize` 추가.
4. `consistency`를 기존 제안 그래프와 통합(+`interrupt` HITL).
5. `planning`(BoardReader) + `change`(abstain/GitHub 위임).
6. `clarify`/가드레일 마감 + 평가 하니스(golden set).

## 10. 확정 결정 (decisions.md)

- **범위(D7)**: 1차 = `lookup` + `locate` + `summarize`. `consistency`는 2차(기존 제안 그래프 통합),
  `change`는 커밋 인덱스 생기면(후순위), `clarify`/가드레일은 상시.
- **planning(D8)**: 채팅 답변 `kind="schedule"` **및** 보드 액션(local 태스크) 양쪽 지원.
- 스트리밍: MVP 이후(열린 결정, decisions.md).
