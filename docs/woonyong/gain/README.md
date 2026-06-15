# 가인

이 폴더는 가인의 `gain` 브랜치 구현 기록, 일 단위 아카이브, 검토 보고서를 모은다.

## 인물

- 이름: 가인
- Git 작성자: `ummfieg <ummfieg@naver.com>`
- GitHub 계정: [`ummfieg`](https://github.com/ummfieg)

## 연결 프로젝트

- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`gain`](https://github.com/Jungle-303-04/warm-up/tree/gain)
- 최근 확인 커밋: [`48b1cc2`](https://github.com/Jungle-303-04/warm-up/commit/48b1cc2fd440c427ebeb168ecbfad13e26948024) `feat: font 가이드 Rag dataset 추가`
- 확인 시각: `2026-06-13 23:00:37 +0900`

## 문서 목록

- [가인 커밋 진화 분석](./commit-evolution-analysis.md)
- [2026-06-10 구현 아카이브](./2026-06-10-implementation-archive.md)
- [2026-06-11 구현 아카이브](./2026-06-11-implementation-archive.md)
- [2026-06-12 구현 아카이브](./2026-06-12-implementation-archive.md)
- [2026-06-13 구현 아카이브](./2026-06-13-implementation-archive.md)
- [2026-06-11 warm-up 백엔드 CRUD 분석](./2026-06-11-warm-up-backend-crud-analysis.md)

## 현재 스냅샷

가인은 AI 폰트 추천 앱의 초기 백엔드 기반을 만들고 있다. 작업은 프론트/백엔드 연결 확인과 DB 모델링, `/posts` CRUD API, 폰트 데이터 크롤링을 지나 `/recommend`에서 OpenAI 분석과 후보 폰트 선택을 수행하는 단계로 넘어갔다.

첫 커밋부터 지금까지의 구현 흐름은 다음과 같다.

1. React + Vite 프론트엔드 초기화
2. FastAPI 백엔드와 health endpoint 추가
3. SQLModel 기반 DB 연결
4. `Font`, `Post`, `User` 테이블 정의
5. `/posts` 목록 조회의 첫 실제 DB 쿼리 추가
6. 게시글 생성/상세/수정/삭제 API 실제 구현
7. 목록/상세 응답을 화면에 필요한 필드 중심으로 축소
8. 등록/수정 시 제목과 내용 빈 값 검증 추가
9. `Font` 모델을 JSON 기반 데이터 구조로 확장
10. 눈누 폰트 상세/목록 크롤러 추가
11. `/recommend` 요청 모델과 기본 응답 구조 추가
12. OpenAI client 모듈과 `/recommend` 문장 분석 호출 추가
13. DB의 `Font` 후보 목록을 OpenAI 선택 prompt에 전달
14. 추천 응답 schema를 `BaseModel`로 정리
15. 폰트 선택 가이드 RAG 데이터셋 추가

## 계속 볼 지점

- 요청/응답 스키마가 DB 테이블 모델과 분리되는가?
- 상세 조회의 “게시글 없음” 응답이 `404`로 통일되는가?
- 잘못된 `font_id`, `user_id`에 대한 검증이 추가되는가?
- 크롤러 실행 코드가 `tests/`에서 별도 실행 스크립트로 분리되는가?
- `/recommend`가 선택된 `font_id`의 실제 `Font` 상세를 반환하는가?
- `font_guides.json`이 실제 RAG 검색/주입 흐름에 연결되는가?
- OpenAI JSON 파싱 실패와 API 키 누락을 안전하게 처리하는가?
- 팀원이 재현할 수 있도록 DB 실행 방법이 문서화되는가?
- 인증을 지금 범위에 넣을지, 임시 `user_id`로 미룰지 결정되는가?
- 목록/상세에서 반복되는 응답 딕셔너리가 스키마나 헬퍼로 정리되는가?
