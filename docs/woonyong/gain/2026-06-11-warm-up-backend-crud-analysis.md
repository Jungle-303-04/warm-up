# 2026-06-11 warm-up 백엔드 CRUD 분석

## 대상

- 인물: [가인](./README.md)
- 저장소: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- 브랜치: [`gain`](https://github.com/Jungle-303-04/warm-up/tree/gain)
- 작성자: `ummfieg <ummfieg@naver.com>`
- 최근 확인 커밋: [`ebbef70`](https://github.com/Jungle-303-04/warm-up/commit/ebbef7056201317e144e8acc1f336754ef272f3a)
- 커밋 메시지: `chore: crud api 의사코드 작성`
- 확인 시각: `2026-06-11 01:34:10 +0900`

## 구현한 내용

가인은 AI 폰트 추천 앱의 초기 풀스택 뼈대를 만들었다.

- 프론트엔드: React + Vite 앱을 만들고, 브랜드 설명 입력창, 추천 버튼, 백엔드 `/health` 호출을 연결했다.
- 백엔드: FastAPI 앱에 `/`, `/health`, `localhost:5173` CORS 설정, `/posts` 라우트를 추가했다.
- DB 연결: `.env`의 `DATABASE_URL`을 읽고 SQLModel 엔진을 생성하도록 구성했다.
- DB 초기화: `init_db.py`에서 모델을 불러온 뒤 `SQLModel.metadata.create_all(engine)`로 테이블을 만들도록 했다.
- 모델:
  - `Font`: 폰트 이름, 출처, 라이선스, 카테고리, 태그, 설명, 굵기, 웹폰트 URL, 원본 URL 같은 폰트 메타데이터를 담는다.
  - `User`: 닉네임, 비밀번호 해시, 생성 시각을 담는다.
  - `Post`: 제목, 내용, `font_id`, `user_id`, 생성 시각, 수정 시각을 담는다.
- API 진행 상태:
  - `GET /posts`는 DB 세션을 열고 `select(Post).all()`로 게시글 목록을 반환하는 실제 구현까지 들어갔다.
  - `POST /posts`, `GET /posts/{post_id}`, `PUT /posts/{post_id}`, `DELETE /posts/{post_id}`는 아직 의사코드와 자리표시자 상태다.

## 고려한 점

코드 주석을 보면 가인은 단순히 테이블만 만드는 수준을 넘어 API 사용 흐름까지 생각하고 있다.

- 게시글 목록에서는 제목, 폰트 미리보기, 폰트 태그처럼 화면에 필요한 정보만 반환하는 방식을 고민했다.
- 게시글 생성 API는 생성 후 상세 페이지로 이동하거나 목록을 바로 갱신할 수 있는 데이터를 반환해야 한다고 봤다.
- 프론트엔드에서 검증을 하더라도 백엔드 검증이 필요하다고 적었다.
- 게시글은 폰트와 작성자 모두에 연결되어야 한다고 판단했다.
- 게시글 생성 시 동시성 문제가 생길 수 있다는 점도 미리 떠올렸다.

## 잘한 점

- 작업 순서가 좋다. 연결 확인, DB 연결, 테이블 모델링, API 설계 순서로 차근차근 넓혀 갔다.
- `font_id`, `user_id`를 통해 게시글과 폰트, 작성자의 관계를 일찍 잡았다.
- 주석이 단순 설명이 아니라 다음 구현 의도를 드러내는 설계 메모 역할을 한다.
- `GET /posts`를 먼저 구현한 것은 좋은 첫 단위다. FastAPI, SQLModel 세션, 테이블 조회가 함께 동작하는지 확인할 수 있기 때문이다.

## 부족하거나 위험한 점

- 대부분의 CRUD 라우트가 아직 실제 구현이 아니고 빈 응답 또는 의사코드에 머물러 있다.
- 요청 스키마와 응답 스키마가 DB 테이블 모델과 분리되어 있지 않다.
- `database.py`가 import 시점에 연결 확인과 출력까지 수행한다. 테스트나 서버 시작 시 예기치 않은 부작용이 생길 수 있다.
- 백엔드 의존성, `.env`, DB 초기화, 서버 실행 방법이 아직 문서로 충분히 보이지 않는다.
- `updated_at`은 기본값만 있고 게시글 수정 시 갱신하는 로직이 없다.
- `tags`, `weights`를 일반 문자열로 저장하고 있다. 초기 구현으로는 괜찮지만 필터링이나 검색이 필요해지면 약해질 수 있다.
- `User` 모델이 이미 생겼는데도 `main.py` 주석에는 user table이 아직 없다는 식의 낡은 설명이 남아 있다.

## 개선 제안

당장 개선은 작게 끊어서 가는 것이 좋다.

1. API 스키마를 먼저 추가한다.
   - `PostCreate`
   - `PostRead`
   - `PostUpdate`
2. CRUD 라우트를 하나씩 완성한다.
   - 먼저 `POST /posts`를 구현한다.
   - 다음으로 `GET /posts/{post_id}`에 404 처리를 넣는다.
   - 그 다음 `PUT /posts/{post_id}`에서 `updated_at`을 갱신한다.
   - 마지막으로 `DELETE /posts/{post_id}`를 구현한다.
3. 인증은 잠시 범위 밖으로 둔다.
   - 임시 `user_id` 입력 또는 seed user를 사용한다.
   - 로그인/비밀번호 구현이 CRUD 학습을 막지 않게 한다.
4. DB 연결 확인 코드는 import 시점에서 실행되지 않도록 분리한다.
5. 백엔드 실행 문서를 추가한다.
   - 의존성 설치
   - `.env.example`
   - DB 초기화 명령
   - 서버 실행 명령
6. 게시글 목록 응답에 폰트 정보를 어디까지 펼쳐서 줄지 결정한다.

## 막힘 신호

- 기본 CRUD가 끝나기 전에 동시성 고민으로 생각이 커지고 있을 가능성이 있다.
- API 요청/응답 모양이 아직 확정되지 않아 구현이 느려질 수 있다.
- 사용자/인증 범위가 불명확해서 `Post` 구현까지 같이 흔들릴 수 있다.
- DB 실행 방법은 본인 환경에서는 알지만 팀원이 재현하기 어려운 상태일 수 있다.

## 사용자가 도울 수 있는 말과 행동

가장 좋은 개입은 불확실성을 줄여 주는 것이다.

- “동시성은 나중에 보고, 지금은 기본 CRUD 먼저 끝내자”라고 범위를 줄여 준다.
- 첫 `POST /posts` 요청 바디를 함께 정한다.
- 로그인 기능을 지금 할지, 임시 `user_id`로 미룰지 결정해 준다.
- 샘플 폰트 데이터 2-3개와 샘플 게시글 흐름 1개를 제공한다.
- CRUD가 한 번 동작한 뒤 백엔드 실행 절차를 문서화해 달라고 요청한다.

## 볼트 연결 기준

볼트 운영 기준은 새 최상위 `people/` 폴더를 만들지 않고 기존 볼트 구조를 재사용하는 것이다.

볼트 쪽 위치는 다음과 같다.

- 사람 노트: `/Users/woonyong/workspace/vault/wiki/common/person-lim-gain.md`
- 프로젝트 노트: `/Users/woonyong/workspace/vault/wiki/career/project-warm-up.md`
- 사람별 프로젝트 분석: `/Users/woonyong/workspace/vault/wiki/career/project-warm-up-lim-gain-analysis.md`

Obsidian 링크 모델은 다음과 같다.

- `[[people-index|사람 관계 인덱스]] -> [[person-lim-gain|임가인]]`
- `[[portfolio-project-moc|팀 프로젝트]] -> [[project-warm-up|warm-up 프로젝트]]`
- `[[project-warm-up|warm-up 프로젝트]] -> [[project-warm-up-lim-gain-analysis|임가인 warm-up 작업 분석]]`

운영 규칙은 다음과 같다.

- 사람 기록은 `wiki/common/person-*.md`에 둔다.
- 프로젝트 요약과 사람별 프로젝트 분석은 `wiki/career/`에 둔다.
- 분석 문서에는 `analysis_date`, `branch_head_sha`, repo URL, branch URL, 작성자 정보를 유지한다.
- 이메일과 평가성 메모가 들어갈 수 있으므로 `access: private`를 유지한다.
