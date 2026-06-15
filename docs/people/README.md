# 인물별 작업 분석

이 폴더는 더 이상 새 인물별 작업 분석 위치로 사용하지 않는다.

사람 노트와 사람 중심 관계는 볼트에서 관리한다. 프로젝트 저장소 안에서는 `docs/woonyong/{person-slug}/` 아래에 구현 검토 아카이브만 둔다.

## 운영 결정

- 사람 노트: `/Users/woonyong/workspace/vault/wiki/common/person-*.md`
- 프로젝트 노트: `/Users/woonyong/workspace/vault/wiki/career/project-*.md`
- 프로젝트 저장소 구현 아카이브: `docs/woonyong/{person-slug}/`
- `docs/people/{person-slug}/`는 볼트 사람 노트와 역할이 겹치므로 사용하지 않는다.

## 정리 기준

- 인물의 관계, 성향, 도움 요청 방식, 프로젝트 분석 링크는 볼트 사람 노트에 둔다.
- 저장소 내부에는 구현 근거, 커밋 흐름, UML, 하루 단위 아카이브만 둔다.
- 다른 인물도 같은 원칙을 따른다.

## 현재 상태

- 신규 인물별 구현 분석은 `docs/woonyong/{person-slug}/`에 둔다.
- 기존 `docs/people/` 하위 사람 폴더가 남아 있으면 같은 기준으로 이동한다.
