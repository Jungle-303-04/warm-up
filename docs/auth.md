# Auth

## Scope

- 회원가입
- 로그인
- JWT 발급 및 검증

## Goal

사용자가 계정을 만들고 로그인한 뒤, 인증된 상태로 다른 기능을 사용할 수 있어야 한다.

## Independent Assumption

- 프로젝트 기능이 아직 없어도 된다.
- 게시글 기능이 아직 없어도 된다.
- 인증 성공 후 임시로 `/me` 같은 간단한 확인 API만 있어도 개발 가능하다.

## Main Work

- 회원가입 API
- 로그인 API
- JWT access token 처리
- 인증이 필요한 API에서 사용자 식별

## Dependency Boundary

- 이후 다른 모듈은 `현재 로그인 사용자` 정보를 이 모듈에서 받아 쓴다.
- 다른 모듈 개발 시 auth는 이미 구현되었거나 mock 가능하다고 가정한다.
