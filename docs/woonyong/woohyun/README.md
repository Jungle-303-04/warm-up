# 우현

이 문서는 개인 프로필이 아니라 이 repo에서 `woohyun` 브랜치 담당 작업을
다시 찾기 위한 구현 분석 입구다. 사람 자체에 대한 긴 설명은 두지 않고,
브랜치, 주요 구현 범위, 검증 기준, 코드 근거 문서만 연결한다.

## repo 관찰 기준

- GitHub author: `JEONWOOHYUN-hydromel <haeli0312@gmail.com>`
- Git author: `woohyun <haeli0312@gmail.com>`
- 관찰 저장소: `Jungle-303-04/warm-up`
- 관찰 브랜치: `origin/woohyun`
- 최신 확인 HEAD: `070d2b4f03596efada8b9c81aebefd311f2062db`
- 최신 확인 시각: `2026-06-12 13:23:20 +0900`

## 현재 관찰 포인트

- 우현은 `AI Team Sync Board`를 Notion, GitHub, 게시판 작업 로그를 묶는 프로젝트 관리형 게시판으로 잡았다.
- 구현은 기획서 정리 이후 FastAPI, PostgreSQL, React 세로 흐름을 한 번에 뚫는 방식으로 진행됐다.
- 현재 브랜치는 게시글 CRUD, JWT 인증, 댓글, 태그, 검색, 페이징, Notion 문서 조회, GitHub 대시보드 조회까지 들어가 있다.
- 아직 AI 요약, RAG, MCP는 실제 구현 전이며, 외부 API 데이터를 화면에 보여주는 준비 단계에 가깝다.

## 담당자 운영 메모

- 앞으로 우현 브랜치를 볼 때는 `origin/woohyun`을 먼저 fetch하고 최신 HEAD를 기준으로 분석한다.
- 작업트리가 더러우면 브랜치를 전환하지 않고 `git show origin/woohyun:path`로 읽는다.
- 긴 인물 평가는 남기지 않고, 구현 분석은 코드와 커밋 근거로만 작성한다.
- 이 repo 문서는 repo만 열어도 읽히도록 유지하고, 볼트 문서를 필수 의존 링크로 만들지 않는다.

## 연결 문서

- [warm-up woohyun 브랜치 구현 분석](./warm-up-woohyun-analysis.md)
