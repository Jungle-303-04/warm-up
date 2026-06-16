# AI Dev Workspace

현재 제품 기획명은 `RepoLM`이다.

RepoLM은 사용자가 GitHub로 로그인해 repo를 선택하면 branch, 문서, 코드, 이슈, PR, 커밋을 자동 분석하고, 작업 상태와 문서 최신성, 다음 action을 근거와 함께 제안하는 repo-first 협업툴이다.

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
- [15. 현재 구현 클래스 UML](./15-current-class-uml.md)
- [16. Repo RAG 구축 통합 계획서](./16-repo-rag-implementation-plan.md)

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
- 현재 구현 클래스 관계는 `15-current-class-uml.md`에 둔다.
- Repo RAG 저장, sync, chunk, embedding 구현 순서는 `16-repo-rag-implementation-plan.md`에 둔다.

## MVP 범위

MVP는 다음을 증명한다.

1. GitHub OAuth로 로그인하고 접근 가능한 repo를 선택할 수 있다.
2. 선택한 repo의 default/open PR/recent active branch를 자동 sync할 수 있다.
3. README/docs, 코드, 이슈, PR, 커밋을 source chunk로 인덱싱할 수 있다.
4. stale document, partial feature, missing test 같은 finding을 보여줄 수 있다.
5. GitHub issue 생성/상태 변경, comment, 문서 수정은 proposal로 만들고 승인 후 실행할 수 있다.
6. repo 연결 해제 시 내부 인덱스와 검색 결과를 제거할 수 있다.

## 명시적으로 제외

- 완전한 Notion 클론
- 완전한 GitHub Projects 클론
- 승인 없는 GitHub write action
- MVP 단계의 완전한 VS Code extension
- public viewer의 편집 기능
- code repo 직접 자동 commit/merge
