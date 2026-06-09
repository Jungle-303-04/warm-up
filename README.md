# SW_AI-W15 Warm-up

문서 기반으로 기술 로드맵, AI 구현 구조, RepoPilot 제품 기획을 정리하는 워크스페이스다.

## Root Documents

- [docs/README.md](./docs/README.md): 세부 문서 인덱스
- [운영 컨벤션](./docs/config/conventions.md): 팀 운영, 문서, Git, Notion 사용 규칙
- [스킬 지도](./docs/skills/README.md): 프로젝트에서 다루는 기술 스킬과 학습/정리 기준

## Document Groups

- [풀스택 기술 로드맵](./docs/woonyong/full-stack-tech-loadmap/README.md)
- [AI 구현 로드맵](./docs/woonyong/ai-implementation/README.md)
- [AI 개발 워크스페이스 / RepoPilot](./docs/woonyong/ai-dev-workspace/README.md)

## Local Pipeline

RepoPilot의 최소 실행 골격은 Docker Compose와 `mise` 기준으로 관리한다.

```bash
mise install
mise run setup
mise run compose:up
```

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/health`
- 세부 계획: [최소 파이프라인 구현 계획](./docs/woonyong/ai-dev-workspace/13-minimal-pipeline-plan.md)
