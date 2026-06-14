# warm-up frontend

React + Vite client for testing the warm-up GitHub OAuth endpoints.

## Local run

```bash
npm install
npm run dev
```

The API base URL defaults to `/api`, and Vite proxies it to
`http://localhost:8000`.

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

When the frontend runs inside Docker, set the proxy target:

```bash
VITE_PROXY_TARGET=http://host.docker.internal:8000 npm run dev
```
