# Bruno API Collection

이 폴더는 Bruno API client에서 바로 열 수 있는 파일 기반 API 컬렉션입니다.

## 열기

1. Bruno 실행
2. `Open Collection` 또는 `Import Collection`
3. 컬렉션 폴더 선택:
   `bruno/warm-up-api`
4. environment는 `local` 선택

## 포함된 요청

- System: root health, OpenAPI schema
- Board: basic/schedule/proceedings 생성, 목록, 단건 조회, 수정, 삭제
- RAG: GitHub 파일 응답 기반 chunk 생성, SQL + Chroma 저장, run 상세 조회, SQL chunk 검색, Chroma vector 검색

## 기준 서버

- API: `http://localhost:8000`
- Chroma: `http://localhost:8001`
- Postgres: `localhost:5432`

Bruno는 컬렉션을 plain text 파일로 저장하므로 이 폴더를 Git으로 관리하면 됩니다.
