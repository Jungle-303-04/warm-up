# Docs

기존 `README.md`는 전체 방향을 보는 메인 문서로 유지한다.
여기서는 개발을 독립적으로 진행할 수 있도록 기능 모듈 단위로 문서를 분리한다.

## Documents

- [auth.md](./auth.md)
  - 회원가입, 로그인, JWT 인증
- [projects.md](./projects.md)
  - 프로젝트 생성과 멤버 추가
- [posts-and-comments.md](./posts-and-comments.md)
  - 게시글, 댓글, 페이징, 검색, 태그
- [ai-writing-and-classification.md](./ai-writing-and-classification.md)
  - AI 초안 작성, 회의록 정리, 카테고리/태그 추천
- [rag.md](./rag.md)
  - RAG, ChromaDB, 프로젝트 문맥 검색
- [agent.md](./agent.md)
  - 싱글 에이전트 흐름과 실행 계획 제안
- [github-integration.md](./github-integration.md)
  - GitHub MCP/API 연동

## Rule

- 각 문서는 다른 기능이 아직 없거나 mock 상태여도 설계할 수 있어야 한다.
- 다른 모듈은 API, 인터페이스, 가짜 데이터로 추상화해도 괜찮다는 전제로 정리한다.
- 문서마다 책임 범위와 외부 의존성을 분리해서 적는다.
