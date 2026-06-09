# AI Dev Workspace

현재 제품 기획명은 `RepoPilot`이다.

RepoPilot은 개발팀이 문서, 일감, 일정, GitHub 이슈, 실제 코드의 관계를 한 프로젝트 안에서 관리하고, 그 결과를 정적 프로젝트 아카이브로 퍼블리싱할 수 있게 하는 협업툴이다.

## 핵심 방향

Notion 전체를 복제하지 않는다. 대신 다음 한 가지를 선명하게 검증한다.

> 프로젝트 문서와 코드가 얼마나 연결되어 있고, 어디가 최신 코드와 어긋났는지 보여준다.

## 문서 목록

- [00. 제품 기획서](./00-product-plan.md)
- [01. 참고 리서치](./01-reference-research.md)
- [02. 제품 요구사항](./02-product-requirements.md)
- [03. 정보 구조](./03-information-architecture.md)
- [04. 시스템 아키텍처](./04-system-architecture.md)
- [05. 실시간 UI와 협업](./05-realtime-ui-and-collaboration.md)
- [06. GitHub 프로젝트와 에이전트 워크플로우](./06-github-projects-and-agent-workflows.md)
- [07. 로드맵과 개발 항목](./07-roadmap-and-development-items.md)
- [08. 저장소, 퍼블리싱, 권한, 보안](./08-storage-publish-permissions-security.md)
- [09. 온보딩과 초기 설정 자동화](./09-onboarding-and-setup-automation.md)
- [10. Web, PWA, Desktop 배포 전략](./10-web-pwa-desktop-distribution.md)
- [11. AI Agent와 RAG 계획](./11-ai-agent-rag-plan.md)
- [12. Python 백엔드 아키텍처](./12-python-backend-architecture.md)
- [13. 최소 파이프라인 구현 계획](./13-minimal-pipeline-plan.md)
- [14. 최소 구현 라인별 해설](./14-minimal-implementation-line-by-line.md)

## 정리 원칙

이 문서 묶음은 다음 기준으로 병합했다.

- 제품 방향과 MVP 컷라인은 `00-product-plan.md`에 모은다.
- 사용자 요구사항은 `02-product-requirements.md`에 둔다.
- 페이지/일감/일정/회의록/위키의 공통 속성 모델은 `03-information-architecture.md`에 둔다.
- GitHub, RAG, worker, publish 흐름은 `04-system-architecture.md`에 둔다.
- 실시간 협업과 정적 뷰어의 차이는 `05-realtime-ui-and-collaboration.md`에 둔다.
- 초대/권한/RAG 보안은 `08-storage-publish-permissions-security.md`에 통합한다.
- AI agent catalog와 retrieval 전략은 `11-ai-agent-rag-plan.md`에 통합한다.
- FastAPI worker, Python OOP 용어, UML deep dive는 `12-python-backend-architecture.md`에 필요한 만큼만 남긴다.
- Docker Compose, mise, worker 실행 순서는 `13-minimal-pipeline-plan.md`에 둔다.

## MVP 범위

MVP는 다음을 증명한다.

1. 프로젝트에 여러 GitHub repo를 연결할 수 있다.
2. 문서와 일감을 하나의 타입 기반 모델로 관리할 수 있다.
3. 일감은 table, kanban, calendar로 볼 수 있다.
4. 문서는 관련 코드 칩을 보여줄 수 있다.
5. 코드 변경 이후 문서 링크 상태가 verified/stale/broken/suggested로 표시된다.
6. 정적 viewer는 읽기 전용 페이지, 검색, 필터, 코드 링크 상태를 제공한다.
7. AI는 근거와 승인 흐름을 가진 proposal만 만든다.

## 명시적으로 제외

- 완전한 Notion 클론
- 완전한 GitHub Projects 클론
- 승인 없는 GitHub write action
- MVP 단계의 완전한 VS Code extension
- public viewer의 편집 기능
- code repo 직접 자동 commit/merge
