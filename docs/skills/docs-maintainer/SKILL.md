---
name: docs-maintainer
description: Use when adding, moving, renaming, deleting, or reorganizing project documentation; update docs indexes, links, folder placement, and stale references so the documentation stays easy for teammates to navigate.
---

# Docs Maintainer

## 기준

문서는 많이 쓰는 것보다 찾기 쉽게 두는 게 먼저다.
새 문서를 만들면 반드시 인덱스와 링크까지 같이 본다.

이 프로젝트의 문서 기준은 `docs/`다.
루트에는 실행 입구와 설정만 두고, 문서 성격의 자료는 `docs/` 아래에 둔다.

## 위치 기준

- 공통 운영 규칙: `docs/config/`
- 팀 공유 스킬: `docs/skills/`
- 풀스택 학습 문서: `docs/woonyong/full-stack-tech-loadmap/`
- AI 구현 학습 문서: `docs/woonyong/ai-implementation/`
- RepoLM 제품 기획: `docs/woonyong/ai-dev-workspace/`

새 문서 위치가 애매하면 먼저 가장 가까운 기존 README의 분류를 따른다.

## 작업 순서

1. `docs/README.md`와 관련 하위 `README.md`를 먼저 확인한다.
2. 문서가 들어갈 폴더를 정한다.
3. 새 문서, 이동 문서, 삭제 문서를 처리한다.
4. 인덱스 링크를 갱신한다.
5. `rg`로 낡은 경로와 제목을 찾는다.
6. 링크가 깨질 가능성이 있으면 상대 경로를 다시 확인한다.
7. 변경 요약에 문서 위치와 인덱스 반영 여부를 남긴다.

## 링크 규칙

- 같은 `docs/` 안에서는 상대 링크를 쓴다.
- 문서 제목을 바꾸면 기존 제목을 `rg`로 찾아 같이 갱신한다.
- 파일을 이동하면 예전 경로를 `rg`로 찾아 같이 갱신한다.
- 새 문서는 가장 가까운 README에 링크한다.

## 작성 규칙

- 한국어로 작성한다.
- 기술명, API, 라이브러리명은 공식 영문 표기를 유지한다.
- 문서 첫 문단에서 목적을 바로 말한다.
- 오래될 수 있는 내용은 `검토 필요` 또는 기준 날짜를 남긴다.
- 코드나 구현 근거가 있으면 파일 경로를 함께 남긴다.

## 피할 것

- 루트에 새 문서 흩뿌리기
- README 인덱스 없이 문서만 추가하기
- 같은 의미의 문서를 이름만 바꿔 중복 생성하기
- 실제 파일 이동 없이 링크만 바꾸기
- 낡은 경로를 남긴 채 마무리하기
