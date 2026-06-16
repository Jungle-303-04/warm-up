# RepoLM Bruno API Collection

Bruno collection for the local RepoLM FastAPI server.

## Environment

- Collection path: `backend/bruno/repolm-api`
- Environment: `local`
- `baseUrl`: `http://localhost:8000`
- `githubRepositoryUrl`: `https://github.com/Jungle-303-04/warm-up.git`

## Requests

| Folder | Request | Method | Path | Expected result |
|---|---|---:|---|---|
| `meta` | Root redirects to docs | GET | `/` | `200`, `307`, or `308` |
| `meta` | Swagger UI | GET | `/docs` | `200` |
| `health` | Health check | GET | `/health` | `{"status":"ok"}` |
| `pipeline` | List pipeline stages | GET | `/pipeline` | non-empty `stages` array |
| `pipeline` | Run default pipeline | POST | `/pipeline/run` | sample repository pipeline result |
| `pipeline` | Run pipeline with inline files | POST | `/pipeline/run` | result for `demo/inline` |
| `pipeline` | Run pipeline with GitHub repository | POST | `/pipeline/run` | synced repository files |
| `pipeline` | Run pipeline with invalid repository URL | POST | `/pipeline/run` | `400` validation error |
| `pipeline` | Sync Repo RAG with inline files | POST | `/pipeline/sync` | succeeded manual sync job |
| `pipeline` | Sync Repo RAG with GitHub repository | POST | `/pipeline/sync` | succeeded sync job |
| `pipeline` | Sync Repo RAG with invalid repository URL | POST | `/pipeline/sync` | `400` validation error |

## Run Targets

The API should be running before executing the collection.

```bash
curl -fsS http://localhost:8000/health
make api-smoke
```

If the Bruno CLI is installed, run from this directory with the local environment.

```bash
bru run --env local
```

The current local machine may have the Bruno desktop app installed without the `bru` CLI on `PATH`.
