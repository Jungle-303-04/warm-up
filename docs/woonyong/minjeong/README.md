# 민정

이 폴더는 민정의 `minjeong` 브랜치 구현 분석, 하루 단위 작업 아카이브,
클래스 단위 시각화 자료를 모아두는 공간이다.

파일명과 경로는 저장소 관리 편의를 위해 영어로 유지하지만, 문서 본문은
한국어로 작성한다.

## 현재 스냅샷

- 저장소: `Jungle-303-04/warm-up`
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 확인 커밋: `23297e5 chore: enable backend hot reload in Docker`
- 확인 시각: `2026-06-11 20:34:46 +09:00`

## 아카이브

- [2026-06-11 warm-up Board 모델 분석](./2026-06-11-warm-up-board-model-analysis.md)

## 시각 자료

- [Board 클래스 UML](./class-uml.md): 현재 구현된 SQLAlchemy 모델을 기준으로 만든 Mermaid 클래스 다이어그램

## 구현 읽기

최신 구현은 초기 스캐폴드에서 한 단계 나아가 `board` 도메인의 SQLAlchemy
모델링으로 이동했다.

- `backend/app/db/base.py`
- `backend/app/domains/board/model.py`
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

현재 브랜치는 `POST /board/` create endpoint와 `CreateBoard` DTO까지
진행됐다. 다만 service는 아직 `return 1` stub이고 repository/DB session이
연결되지 않았으므로, 실제 Board 생성은 아직 구현 전이다.

## RAG/Agent/MCP 관점

현재 Board 모델은 일반 협업 보드의 출발점으로는 괜찮지만, RAG, Agent, MCP
실행 기록까지 담는 전체 모델로 보기에는 아직 중심 도메인만 있는 상태다.
AI 관련 데이터는 Board 테이블에 섞기보다 나중에 `Document`, `Chunk`,
`RetrievalLog`, `AgentRun`, `ToolCall`, `McpServer`, `McpTool` 같은 별도
테이블이 Board나 Project를 참조하는 방식으로 확장하는 편이 좋다.
