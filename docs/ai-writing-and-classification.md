# AI Writing And Classification

## Scope

- AI 게시글 초안 작성
- 회의록 정리
- 카테고리 추천
- 태그 추천
- 저장 방식 추천

## Goal

사용자가 자유 텍스트를 입력하면 AI가 글을 더 잘 쓰게 돕고, 문서를 정리하고 분류하도록 한다.

## Independent Assumption

- 게시글 저장은 아직 없더라도, 입력 텍스트와 출력 결과만으로 먼저 개발 가능하다.
- 프로젝트 맥락이 없어도 단일 문서 기준으로 먼저 구현 가능하다.
- 초기에는 RAG 없이도 동작할 수 있다.

## Main Work

- GPT 호출
- structured output 설계
- 초안 생성 프롬프트
- 회의록 정리 프롬프트
- 분류 추천 프롬프트

## Dependency Boundary

- 이 모듈은 입력 텍스트를 받아 구조화된 결과를 반환하는 역할에 집중한다.
- 저장, 실행, GitHub 연동은 이 모듈 책임이 아니다.
