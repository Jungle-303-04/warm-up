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
- [디버그 실행 이해 노트](./debugging-mental-model.md)
- [Docker 컨테이너 디버그](./docker-debug-guide.md)
- [API 테스트 방법](./api-testing-guide.md)
- [Python import root 기준](./python-import-root-guide.md)
- [UML 렌더링 기준](./uml-rendering-guide.md)
- [mise 사용법](./mise-guide.md)
- [pnpm 사용법](./pnpm-guide.md)

## 처음 볼 순서

1. [mise 사용법](./mise-guide.md): 어떤 버전의 도구를 쓰고 어떤 명령을 실행하는지 이해한다.
2. [pnpm 사용법](./pnpm-guide.md): web app package와 workspace 구조를 이해한다.
3. [Docker Compose 사용법](./docker-compose-guide.md): web, api, worker, DB, Redis가 어떻게 같이 뜨는지 이해한다.
4. [디버그 실행 이해 노트](./debugging-mental-model.md): Docker 실행, debugger attach, API 요청의 차이를 먼저 잡는다.
5. [Docker 컨테이너 디버그](./docker-debug-guide.md): VS Code에서 컨테이너 안의 FastAPI와 Next.js 프로세스에 attach하는 방법을 확인한다.
6. [API 테스트 방법](./api-testing-guide.md): Swagger UI, REST Client, curl로 API를 직접 호출한다.
7. [Python import root 기준](./python-import-root-guide.md): VS Code, Pyright, pytest, Docker의 Python import 기준을 하나로 맞춘다.
8. [UML 렌더링 기준](./uml-rendering-guide.md): 클래스 UML을 One Dark Pro 기준 SVG로 안정적으로 보여주는 방법을 확인한다.
