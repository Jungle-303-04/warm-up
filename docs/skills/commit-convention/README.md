# 커밋 컨벤션 스킬

## 목적

이 문서는 프로젝트에서 커밋 메시지, 브랜치, PR 단위를 정할 때 참고하는 스킬 문서다.

Codex 스킬로 사용할 때는 같은 폴더의 [SKILL.md](./SKILL.md)를 기준으로 한다.

## 기본 형식

```text
<type>: <한국어 제목>
```

예시:

```text
docs: 문서 구조를 docs 하위 폴더로 정리
feat: RepoPilot 최소 파이프라인 API를 추가
fix: draft 저장 응답의 상태 필드를 보정
```

## 허용 타입

- `feat`: 사용자 관점의 기능 추가
- `fix`: 버그 수정
- `refactor`: 동작 변화 없는 구조 개선
- `docs`: 문서 변경
- `test`: 테스트 추가 또는 수정
- `chore`: 유지보수
- `style`: 동작에 영향 없는 포맷팅
- `perf`: 성능 개선
- `build`: 빌드 설정 변경
- `ci`: CI 설정 변경
- `revert`: 이전 커밋 되돌리기

## 판단 기준

- 문서 구조 변경은 `docs`
- 실행 코드의 새 기능은 `feat`
- 실패하던 동작을 고치면 `fix`
- 동작은 같고 구조만 바꾸면 `refactor`
- 의존성, 빌드, 자동화 설정은 `build` 또는 `chore`

## 연결 문서

- [운영 컨벤션](../../config/conventions.md)
- [Codex 스킬](./SKILL.md)
