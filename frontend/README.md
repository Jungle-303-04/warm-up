# warm-up 프론트엔드

warm-up 깃허브 OAuth API를 테스트하기 위한 React + Vite 클라이언트입니다.

## 로컬 실행

```bash
npm install
npm run dev
```

기본 API 주소는 `/api`이며, Vite 개발 서버가 이 요청을
`http://localhost:8000`으로 프록시합니다.

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

프론트엔드를 Docker 안에서 실행할 때는 프록시 대상을 지정합니다.

```bash
VITE_PROXY_TARGET=http://host.docker.internal:8000 npm run dev
```
