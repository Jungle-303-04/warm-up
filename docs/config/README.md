# 설정/운영 문서

이 폴더는 프로젝트의 운영 규칙, 문서 작성 규칙, Git 규칙처럼 코드 실행 파일은 아니지만 반복해서 참조해야 하는 설정성 문서를 모아둔다.

## 문서 목록

- [운영 컨벤션](./conventions.md)

## 루트에 남기는 것과 docs로 옮기는 것

루트에는 실행에 필요한 파일만 둔다.

```text
README.md
package.json
pnpm-workspace.yaml
compose.yaml
.env.example
.mise.toml
apps/
backend/
docker/
```

문서 성격의 파일은 `docs/` 아래로 둔다.

```text
docs/skills/
docs/config/
docs/woonyong/
```

`compose.yaml`, `.env.example`, `.mise.toml`은 설정 파일이지만 실제 실행과 자동화에서 루트 위치를 기대할 수 있으므로 이동하지 않는다. 대신 사용법과 규칙만 이 폴더에서 문서화한다.
