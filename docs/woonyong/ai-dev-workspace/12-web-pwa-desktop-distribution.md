# Web, PWA, and Desktop Distribution

## Capability

`RepoPilot MVP`는 웹앱으로 먼저 만들되, 사용자는 macOS와 Windows에서 앱처럼 설치해 사용할 수 있어야 한다. 별도의 네이티브 앱을 새로 개발하지 않고, 같은 React/Vite frontend를 web, PWA, desktop wrapper에서 공유한다.

## Decision

2주 MVP의 기본 배포 전략은 다음이다.

```text
P0: Web app + Installable PWA
P1: Optional Tauri desktop shell
P2: Native desktop deep integration
```

첫 버전은 웹에서 바로 쓰고, macOS/Windows에서는 PWA로 설치해 앱처럼 실행한다. `.dmg`, `.exe`, `.msi` 같은 설치 파일이 꼭 필요하면 Tauri로 같은 웹앱을 감싼다.

## Why Web First

RepoPilot의 핵심 기능은 서버 중심이다.

- GitHub App auth
- Draft DB autosave
- realtime document sync
- workspace repo auto publish
- AI/RAG search
- issue sync
- audit log

따라서 macOS/Windows 앱도 로컬에서 모든 것을 처리하는 앱이 아니라, 같은 서버에 접속하는 desktop client로 보는 것이 맞다.

## Distribution Options

| 방식 | 장점 | 단점 | MVP 판단 |
|---|---|---|---|
| Web app | 가장 빠름, 배포 쉬움, 팀원 접근 쉬움 | 브라우저 탭처럼 느껴질 수 있음 | 필수 |
| PWA | 설치형 앱 느낌, 같은 코드, 빠른 구현 | 브라우저별 설치 지원 차이 | 필수 |
| Tauri | 작은 desktop wrapper, macOS/Windows 패키지 가능 | Rust/toolchain/서명/업데이트 고려 필요 | P1 또는 필요 시 P0 late |
| Electron | JS 생태계 강함, Chromium 일관성 | 앱 크기/메모리/보안 설정 부담 | MVP 비추천 |

공식 문서 기준 참고:

- Tauri는 웹 frontend를 desktop app으로 가져올 수 있고 cross-platform build를 지원한다. [Tauri](https://tauri.app/)
- Tauri 개발에는 Rust, macOS Xcode Command Line Tools, Windows Microsoft C++ Build Tools/WebView2 같은 준비가 필요하다. [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)
- Electron은 Chromium과 Node.js를 포함해 macOS/Windows/Linux에서 동작하는 desktop app을 만들 수 있다. [Electron](https://www.electronjs.org/)
- PWA는 manifest를 갖추면 설치되어 OS의 앱처럼 실행될 수 있다. [MDN PWA installable](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)

## Recommended MVP Path

### P0: Installable PWA

필수 구현:

- `manifest.webmanifest`
- 192px/512px icon
- app name/short name
- `start_url`
- `display: standalone`
- service worker
- install 안내 UI
- offline fallback page
- app shell caching

PWA는 사용자가 다음처럼 느껴야 한다.

```text
브라우저에서 접속
-> "앱으로 설치" 클릭
-> Dock/Start Menu에서 RepoPilot 실행
-> 브라우저 UI 없이 독립 창으로 사용
```

PWA에서 여전히 서버가 필요한 기능:

- GitHub sync
- AI/RAG
- realtime editing
- auto publish

오프라인에서 가능한 최소 기능:

- 마지막 Home cache 보기
- 최근 draft 보기
- 네트워크 끊김 안내

### P1: Tauri Desktop Shell

Tauri는 같은 Vite build를 desktop window에 올린다.

구조:

```text
apps/web
  React/Vite frontend

apps/server
  Fastify API/realtime/publish worker

apps/desktop
  Tauri shell
  loads web app or bundled frontend
```

Tauri desktop은 두 가지 방식 중 하나를 선택한다.

#### Remote shell

```text
Tauri window
-> https://app.repopilot.dev 로드
```

장점:

- 구현 빠름
- 업데이트 쉬움
- 서버 기능과 자연스럽게 연결

단점:

- 네트워크 필수
- 앱 심사/보안 정책에서 remote content 고려 필요

#### Bundled shell

```text
Tauri window
-> bundled Vite assets 로드
-> API는 서버에 요청
```

장점:

- 앱 실행이 더 네이티브처럼 보임
- 초기 화면 빠름

단점:

- desktop 앱 업데이트 필요
- web/desktop 버전 mismatch 관리 필요

MVP 이후 추천은 `Bundled shell`이다. 2주 안에 꼭 desktop installer가 필요하면 `Remote shell`로 시작한다.

## Desktop Feature Cutline

P1에서 할 것:

- macOS app build
- Windows app build
- app icon
- login/session 유지
- external link open in browser
- update 안내

P2로 미룰 것:

- tray app
- native notification
- global shortcut
- local Git daemon
- local encrypted cache
- offline-first editing
- OS file association

## Auth and Security

desktop app도 GitHub token을 직접 가지면 안 된다.

원칙:

```text
GitHub OAuth login -> server session
GitHub App installation token -> server only
Desktop app -> server API 호출
```

desktop local storage에 저장 가능한 것:

- session id 또는 refresh token
- user preference
- window size
- last workspace id

desktop local storage에 저장하면 안 되는 것:

- GitHub App private key
- GitHub installation token
- repo clone credentials
- OpenAI/API secret

로그아웃 시:

- local session 삭제
- cached user data 삭제
- server session revoke

## Desktop and Auto Publish

desktop app은 publish worker를 직접 실행하지 않는다.

```text
Desktop editor
-> server Draft DB autosave
-> server publish worker
-> workspace repo commit
```

이렇게 해야 macOS 사용자와 Windows 사용자가 동시에 편집해도 publish queue가 한 곳에서 직렬화된다.

## Desktop and Realtime Editing

desktop app도 web app과 같은 realtime endpoint를 쓴다.

```text
Web browser user
Desktop macOS user
Desktop Windows user
-> same realtime document room
-> same Draft DB
-> same publish worker
```

따라서 desktop app은 별도의 협업 로직을 갖지 않는다.

## Build Targets

PWA:

```text
web build
manifest
service worker
HTTPS hosting
```

Tauri:

```text
macOS: .app/.dmg
Windows: .exe/.msi
```

주의:

- macOS 배포에는 code signing/notarization이 필요할 수 있다.
- Windows 배포에는 code signing certificate가 필요할 수 있다.
- 서명 없는 앱은 설치/실행 경고가 뜰 수 있다.

2주 MVP에서는 팀 내부 사용이므로 서명 없는 build 또는 PWA 설치로 시작한다.

## Monorepo Layout

```text
apps/
├── web/
│   ├── src/
│   ├── public/
│   │   ├── manifest.webmanifest
│   │   └── icons/
│   └── vite.config.ts
├── server/
│   ├── src/
│   └── package.json
└── desktop/
    ├── src-tauri/
    ├── package.json
    └── tauri.conf.json
```

공유 패키지:

```text
packages/
├── ui/
├── shared-types/
├── api-client/
└── markdown/
```

## UX Requirement

사용자는 플랫폼 차이를 느끼지 않아야 한다.

동일해야 하는 것:

- Home dashboard
- editor
- autosave status
- publish status
- GitHub issue actions
- AI panel
- approval center

desktop에서 추가로 있으면 좋은 것:

- 앱 아이콘
- 독립 창
- 메뉴바의 Reload/Logout
- 외부 링크는 기본 브라우저로 열기

## MVP Acceptance Criteria

PWA:

- macOS Chrome/Edge/Safari에서 앱처럼 실행 가능
- Windows Chrome/Edge에서 앱처럼 실행 가능
- 앱 아이콘과 이름 표시
- standalone window로 실행
- 로그인 후 Home dashboard 접근 가능

Tauri optional:

- macOS에서 desktop build 실행
- Windows에서 desktop build 실행
- 동일한 서버에 로그인
- Home/Docs/Tasks/Calendar/AI 동작

## Final Recommendation

2주 MVP에서는 PWA를 반드시 넣는다. 이것만으로도 macOS/Windows에서 앱처럼 사용할 수 있다.

Tauri는 "팀이 진짜 설치 파일을 원한다"는 요구가 확정되면 붙인다. 단, desktop shell은 서버 기능을 복제하지 않고 같은 web frontend와 server API를 사용하는 얇은 client로 유지한다.
