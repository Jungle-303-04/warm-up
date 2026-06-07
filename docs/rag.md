# RAG

## Scope

- 문서 임베딩
- ChromaDB 저장
- 관련 청크 검색
- 프로젝트 문맥 검색

## Goal

저장된 문서 중 현재 질문이나 요청과 관련 있는 문맥을 빠르게 찾아 AI가 참고할 수 있게 한다.

## Independent Assumption

- 게시글과 회의록 데이터는 이미 있다고 가정하거나 샘플 텍스트로 대체 가능하다.
- 챗봇이 아직 없어도 검색 모듈만 먼저 구현 가능하다.
- ChromaDB는 보조 저장소이고, 원본은 PostgreSQL에 있다고 가정한다.

## Main Work

- 문서 청크 분리
- 임베딩 생성
- ChromaDB 저장
- 질의 시 관련 청크 retrieval
- 원문 변경 시 벡터 업데이트 전략

## Dependency Boundary

- 이 모듈은 `관련 문맥을 찾아 반환`하는 데 집중한다.
- 최종 답변 생성은 에이전트 또는 GPT 호출 모듈 책임이다.
