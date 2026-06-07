# GitHub Integration

## Scope

- GitHub 저장소 조회
- 이슈 / 프로젝트 조회
- 향후 이슈 생성 / 프로젝트 업데이트

## Goal

프로젝트 문맥과 GitHub 작업을 연결해 개발 관리 흐름으로 확장한다.

## Independent Assumption

- GitHub 연동은 나중에 붙여도 된다.
- AI 없이도 단순 조회 기능부터 먼저 구현 가능하다.
- MCP가 없더라도 GitHub API 기반으로 대체 가능하다.

## Main Work

- GitHub MCP 또는 GitHub API 연결
- 저장소 / 이슈 / 프로젝트 읽기
- 나중에 이슈 생성 / 업데이트 확장

## Dependency Boundary

- 이 모듈은 외부 GitHub 시스템과의 연결 책임을 가진다.
- 어떤 작업을 GitHub에 보낼지 판단하는 책임은 에이전트 쪽에 있다.
