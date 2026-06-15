# 민정

이 폴더는 민정의 `minjeong` 브랜치 구현 분석, 하루 단위 작업 아카이브,
클래스 단위 시각화 자료를 모아두는 공간이다.

파일명과 경로는 저장소 관리 편의를 위해 영어로 유지하지만, 문서 본문은
한국어로 작성한다.

## 현재 스냅샷

- 저장소: `Jungle-303-04/warm-up`
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: `8368026 fix: schedule tasks only for schedule boards`
- 확인 시각: `2026-06-13 18:01:05 +09:00`

## 아카이브

- [민정 warm-up 커밋 진화 분석](./commit-evolution-analysis.md)
- [2026-06-11 warm-up Board 모델 분석](./2026-06-11-warm-up-board-model-analysis.md)
- [2026-06-12 warm-up Board 생성 응답 흐름 분석](./2026-06-12-warm-up-board-create-response-analysis.md)
- [2026-06-13 warm-up Board DB 저장 흐름 분석](./2026-06-13-warm-up-board-db-insert-analysis.md)

## 구현 기준 메모

- [Board API 검증 실패 상태 코드 기준](./board-api-validation-status-policy.md): `400`, `422`, `409`를 나누는 기준

## 시각 자료

- [Board 클래스 UML](./class-uml.md): 현재 구현된 SQLAlchemy 모델을 기준으로 만든 Mermaid 클래스 다이어그램

## 구현 읽기

최신 구현은 초기 스캐폴드에서 한 단계 나아가 `board` 도메인의 SQLAlchemy
모델링으로 이동했다.

- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/domains/board/model.py`
- `backend/app/domains/user/model.py`
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/schema.py`
- `backend/app/domains/board/service.py`

현재 보이는 설계 방향은 계층형 FastAPI 백엔드다.

- `router.py`: Board HTTP 요청을 받는 계층
- `service.py`: 비즈니스 흐름을 처리할 계층
- `repository.py`: SQLAlchemy 영속성 처리를 분리할 계층
- `schema.py`: Pydantic 요청/응답 DTO를 정의할 계층
- `model.py`: Board, 일정 상세, 회의록 상세, 일정 task, Board-User 역할 연결 테이블을 정의하는 계층

현재 브랜치는 `POST /board/` create endpoint에서 출발해 `GET /board/`,
`GET /board/{board_id}`, `PUT /board/{board_id}`, `DELETE /board/{board_id}`까지
Board CRUD 형태로 확장됐다. `BoardSearchParams`, `BoardPageResponse`,
`UpdateBoard`가 추가됐고, repository에는 검색 조건, pagination, 단건 조회,
수정, 삭제, ORM -> DTO 변환 함수가 생겼다. 다만 테스트 부재, repository 책임
비대화, `400`/`422` 기준 미정리, `create_all`, 임시 `User(id=1)` 같은
학습용 구현의 위험은 남아 있다.

## RAG/Agent/MCP 관점

현재 Board 모델은 일반 협업 보드의 출발점으로는 괜찮지만, RAG, Agent, MCP
실행 기록까지 담는 전체 모델로 보기에는 아직 중심 도메인만 있는 상태다.
AI 관련 데이터는 Board 테이블에 섞기보다 나중에 `Document`, `Chunk`,
`RetrievalLog`, `AgentRun`, `ToolCall`, `McpServer`, `McpTool` 같은 별도
테이블이 Board나 Project를 참조하는 방식으로 확장하는 편이 좋다.
