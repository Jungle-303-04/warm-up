# 2026-06-14 warm-up RAG/GitHub 인덱싱 분석

## 범위

- 사람: [민정](./README.md)
- 브랜치: `minjeong`
- 작성자: `minmings111 <minmings111@gmail.com>`
- 최신 대상 커밋: `21b1961 docs: add source code comments`
- 날짜 범위: `2026-06-14`

## 하루 요약

민정은 Board CRUD 이후 RAG와 GitHub 도메인으로 작업 범위를 크게 확장했다.
처음에는 RAG/GitHub domain scaffold를 만들고, 이후 GitHub 파일을 RAG chunk로
바꾸는 pipeline, Python/Markdown chunking, chunk identity/citation, DI container,
router 연결까지 빠르게 넓혔다.

## 시간대별 작업 흐름

### 16:32 - `0d571f3 feat: scaffold RAG and GitHub domains`

- `backend/app/domains/rag/*`, `backend/app/domains/github/*` 기본 파일을 만들었다.
- RAG service에 chunking, 파일 스냅샷, 기본 pipeline 개념을 넣기 시작했다.
- GitHub service는 외부 GitHub 파일 응답을 RAG 입력으로 바꾸기 위한 입구로 보인다.

### 22:04 - `723927e feat: add GitHub RAG indexing pipeline`

- `common/identity.py`, `common/validation.py`를 추가했다.
- `github/schema.py`, `github/service.py`를 확장했다.
- `rag/pipeline.py`, `rag/schema.py`, `rag/service.py`에 GitHub 파일 -> snapshot -> chunk 변환 흐름을 넣었다.
- 구현 의도는 "GitHub 레포 파일을 받아 검색 가능한 evidence chunk로 바꾸는 것"이다.

### 22:26 - `95cdb38 refactor: split RAG chunking modules`

- `chunking.py`, `chunk_identity.py`, `python_classifier.py`로 RAG chunking 책임을 분리했다.
- 기존 `rag/service.py`의 거대한 로직을 module 단위로 쪼갰다.
- Python 파일은 class/function/import 같은 코드 구조를 기준으로 chunk를 나누려는 방향이다.

### 23:31 - `696c85f feat: wire RAG indexing services`

- `container.py`를 추가해 dependency-injector 기반 조립을 시작했다.
- `chunk_factory`, `chunk_citation`, `chunker_registry`, `markdown_chunker`, `python_chunker`,
  `snapshot_validator`, `chunking_service`를 분리했다.
- `rag/router.py`와 `main.py`에 RAG route를 연결했다.
- RAG indexing이 파일 단위 helper 묶음에서 service/pipeline 구조로 올라갔다.

### 23:38 - `21b1961 docs: add source code comments`

- 주요 module에 한국어 주석을 추가했다.
- 학습 목적상 각 class/function의 역할을 명시하려는 커밋이다.
- 주석은 이해에는 도움되지만, 테스트나 API contract를 대체하지는 않는다.

## 무엇을 고려했는가

- GitHub 파일을 그대로 LLM에 넣지 않고 snapshot, chunk, citation으로 나누려 했다.
- Python과 Markdown은 chunking 기준이 다르므로 chunker를 분리하려 했다.
- chunk id/hash/citation을 만들어 나중에 검색 결과의 출처를 추적하려 했다.
- DI container로 service 조립 위치를 한 곳에 모으려 했다.

## 잘한 점

- Board CRUD 이후 RAG/GitHub 도메인으로 확장 방향을 잡았다.
- 거대한 RAG service를 chunking module로 분리한 판단은 맞다.
- citation과 identity를 초기에 고려한 점은 RAG 답변 신뢰도에 중요하다.
- `container.py`로 조립 위치를 만든 것은 이후 auth, RAG, agent를 연결하기 좋은 기반이다.

## 부족하거나 위험한 점

- 기능 범위가 하루 안에 크게 넓어져 테스트 없이 유지하기 어렵다.
- GitHub API 실패, rate limit, binary/large file 제외 정책이 더 명확해야 한다.
- RAG chunk 품질은 unit test와 fixture가 없으면 회귀를 잡기 어렵다.
- DI container가 생겼지만 app startup, test override, env 설정 기준은 아직 약하다.

## 개선 방향

1. Python/Markdown chunking fixture 테스트를 추가한다.
2. GitHub 파일 수집 실패, 빈 파일, 대용량 파일, unsupported file 테스트를 추가한다.
3. citation 형식을 문서와 테스트로 고정한다.
4. DI container test override 기준을 정한다.
5. RAG indexing API의 입력/출력 DTO 예시를 Bruno 또는 문서에 남긴다.

