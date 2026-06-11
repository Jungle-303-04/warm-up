# 가인

이 폴더는 가인의 `gain` 브랜치 구현 기록, 일 단위 아카이브, 검토 보고서를 모은다.

## 인물

- 이름: 가인
- Git 작성자: `ummfieg <ummfieg@naver.com>`
- GitHub 계정: [`ummfieg`](https://github.com/ummfieg)

## 연결 프로젝트

- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`gain`](https://github.com/Jungle-303-04/warm-up/tree/gain)
- 최근 확인 커밋: [`ebbef70`](https://github.com/Jungle-303-04/warm-up/commit/ebbef7056201317e144e8acc1f336754ef272f3a) `chore: crud api 의사코드 작성`
- 확인 시각: `2026-06-11 01:34:10 +0900`

## 문서 목록

- [2026-06-10 구현 아카이브](./2026-06-10-implementation-archive.md)
- [2026-06-11 warm-up 백엔드 CRUD 분석](./2026-06-11-warm-up-backend-crud-analysis.md)

## 현재 스냅샷

가인은 AI Font Recommendation 앱의 초기 백엔드 기반을 만들고 있다. 작업은 프론트/백엔드 연결 확인에서 DB 모델링, `Post`/`User` 모델 추가, `/posts` CRUD API 설계로 넘어갔다.

현재 보이는 구현 흐름은 다음과 같다.

1. React + Vite 프론트엔드 초기화
2. FastAPI 백엔드와 health endpoint 추가
3. SQLModel 기반 DB 연결
4. `Font`, `Post`, `User` 테이블 정의
5. `/posts` 목록 조회의 첫 실제 DB 쿼리 추가
6. 게시글 생성/상세/수정/삭제 API 의사코드 작성

## 계속 볼 지점

- 의사코드가 실제 CRUD 구현으로 넘어가는가?
- 요청/응답 스키마가 DB 테이블 모델과 분리되는가?
- 팀원이 재현할 수 있도록 DB 실행 방법이 문서화되는가?
- 인증을 지금 범위에 넣을지, 임시 `user_id`로 미룰지 결정되는가?
- `Font.tags`, `Font.weights`를 문자열로 둘지 구조화할지 결정되는가?
- 기본 CRUD 전에 동시성 고민으로 구현이 지연되지 않는가?
