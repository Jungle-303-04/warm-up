# API 테스트 방법

이 문서는 RepoPilot API를 Postman 없이 테스트하는 방법을 정리한다.

현재 FastAPI 서버는 실행되면 아래 주소를 제공한다.

| 목적 | 주소 |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Health check | `http://localhost:8000/health` |

## Docker debug API 실행

FastAPI만 Docker debug 모드로 띄우려면 아래 명령을 쓴다.

```bash
mise run compose:debug:api
```

전체 web/api/worker까지 같이 보고 싶으면 아래 명령을 쓴다.

```bash
mise run compose:debug
```

API가 떠 있는지 확인한다.

```bash
mise run api:smoke
```

## Swagger UI로 테스트

브라우저에서 아래 주소를 연다.

```text
http://localhost:8000/docs
```

Swagger UI에서는 다음 엔드포인트를 바로 실행할 수 있다.

- `GET /health`
- `GET /pipeline`
- `POST /pipeline/run`
- `POST /pipeline/sync`

샘플 요청:

```json
{}
```

Repo RAG sync 샘플 요청:

```json
{
  "repository": "demo/repo-rag",
  "branch": "main",
  "trigger_type": "manual",
  "files": [
    {
      "path": "README.md",
      "content": "# Demo\n\nThis file becomes a retrieval chunk.\n"
    },
    {
      "path": "app.py",
      "content": "def run():\n    return True\n"
    }
  ]
}
```

## VS Code REST Client로 테스트

Postman처럼 요청을 저장해두고 실행하려면 VS Code의 REST Client 확장을 쓴다.

1. VS Code 확장 추천에서 `REST Client`를 설치한다.
2. [repopilot.http](../../../backend/requests/repopilot.http)를 연다.
3. 각 요청 위의 `Send Request`를 누른다.

이 파일에는 아래 요청이 들어 있다.

- health check
- pipeline stage 조회
- 기본 pipeline 실행
- inline files pipeline 실행
- public GitHub repository pipeline 실행
- Repo RAG sync 실행

## curl로 테스트

Health check:

```bash
curl -fsS http://localhost:8000/health
```

Pipeline stage:

```bash
curl -fsS http://localhost:8000/pipeline
```

기본 pipeline 실행:

```bash
curl -fsS http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

Repo RAG sync 실행:

```bash
curl -fsS http://localhost:8000/pipeline/sync \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "demo/repo-rag",
    "branch": "main",
    "trigger_type": "manual",
    "files": [
      {
        "path": "README.md",
        "content": "# Demo\n\nThis file becomes a retrieval chunk.\n"
      }
    ]
  }'
```

## 디버그와 함께 보기

FastAPI breakpoint를 걸고 요청을 보내려면 아래 순서로 한다.

1. `mise run compose:debug:api` 실행
2. VS Code에서 `Attach FastAPI in Docker` 선택
3. `backend/app/api/routes/pipeline.py` 또는 `backend/app/services/repo_rag_sync.py`에 breakpoint 설정
4. Swagger UI, REST Client, curl 중 하나로 요청 실행

요청이 breakpoint에서 멈추면 Docker 컨테이너 안의 FastAPI 코드에 정상 연결된 것이다.

