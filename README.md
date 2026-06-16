# SW_AI-W15 Warm-up

문서 기반으로 기술 로드맵, AI 구현 구조, RepoLM 제품 기획을 정리하는 워크스페이스다.

## Documentation

- [문서 인덱스](./docs/README.md): 전체 문서 구조
- [스킬 문서](./docs/skills/README.md): 프로젝트에서 다루는 기술 스킬과 학습/정리 기준
- [설정/운영 문서](./docs/config/README.md): 팀 운영, 문서 작성, Git 규칙

## Document Groups

- [풀스택 기술 로드맵](./docs/woonyong/full-stack-tech-loadmap/README.md)
- [AI 구현 로드맵](./docs/woonyong/ai-implementation/README.md)
- [AI 개발 워크스페이스 / RepoLM](./docs/woonyong/ai-dev-workspace/README.md)

## Local Pipeline

RepoLM의 최소 실행 골격은 Docker Compose와 `mise` 기준으로 관리한다.

```bash
mise install
mise run setup
mise run compose:up
```

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- 세부 계획: [최소 파이프라인 구현 계획](./docs/woonyong/ai-dev-workspace/13-minimal-pipeline-plan.md)
