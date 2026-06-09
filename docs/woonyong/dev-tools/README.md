# 개발 도구 사용법

이 폴더는 RepoPilot 최소 구현을 실행하고 이해하는 데 필요한 개발 도구 문서를 모아둔다.

## 각 도구가 하는 일

| 도구 | 하는 일 | 현재 프로젝트에서 쓰는 이유 |
|---|---|---|
| Docker Compose | 여러 컨테이너를 한 번에 실행한다 | web, api, worker, postgres, redis를 한 번에 띄운다 |
| mise | 개발 도구 버전과 반복 명령을 고정한다 | Node, pnpm, Python, uv 버전과 setup/check 명령을 통일한다 |
| pnpm | JavaScript package를 설치하고 workspace script를 실행한다 | Next.js web app 의존성 설치와 dev/build/typecheck 실행에 쓴다 |

## 문서 목록

- [Docker Compose 사용법](./docker-compose-guide.md)
- [mise 사용법](./mise-guide.md)
- [pnpm 사용법](./pnpm-guide.md)

## 처음 볼 순서

1. [mise 사용법](./mise-guide.md): 어떤 버전의 도구를 쓰고 어떤 명령을 실행하는지 이해한다.
2. [pnpm 사용법](./pnpm-guide.md): web app package와 workspace 구조를 이해한다.
3. [Docker Compose 사용법](./docker-compose-guide.md): web, api, worker, DB, Redis가 어떻게 같이 뜨는지 이해한다.
