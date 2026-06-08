# Web, PWA, Desktop 배포 전략

## 결정

Web을 먼저 만든다. Workspace app은 installable PWA로 제공한다. Native desktop은 core product가 아니라 후속 shell로 취급한다.

## Web First 이유

- GitHub OAuth와 팀 온보딩이 쉽다.
- Static viewer 배포가 web-native다.
- 협업 기능을 공유하기 쉽다.
- 사용자가 desktop app 설치 없이 평가할 수 있다.

## MVP 배포 방식

MVP:

- hosted web app
- installable PWA
- static published viewer

MVP 제외:

- full Tauri app
- local background daemon
- offline-first editing
- deep native file watching

## 로컬 코드 열기

Browser에서 local code를 열 때는 사용자가 local repo path를 설정한 경우 VS Code URI를 사용한다.

동작 예시:

```text
local repo configured -> vscode://file/<path>:<line>
local repo missing    -> GitHub permalink/current URL
```

항상 GitHub fallback을 제공해야 한다.

## Desktop 후속

Desktop shell이 유용해지는 시점:

- local repo path 관리가 중요해질 때
- file watching이 stale detection 품질을 높일 때
- local embedding이 필요할 때
- offline authoring이 필요할 때
- VS Code extension 연동이 성숙했을 때

P1/P2 선택지:

- macOS/Windows용 Tauri shell
- VS Code extension
- local companion service

## Static Viewer 배포

Static output은 다음 대상에 배포 가능해야 한다.

- built-in hosted pages
- GitHub Pages
- Cloudflare Pages
- Vercel
- Netlify

MVP는 managed target 하나와 local/export artifact로 시작해도 충분하다.
