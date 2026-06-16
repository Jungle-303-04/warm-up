.PHONY: help setup test check compose-config api-typecheck api-test web-typecheck api-smoke compose-up compose-debug compose-debug-api compose-down compose-logs

.DEFAULT_GOAL := help

help:
	@printf "RepoLM commands\n"
	@printf "\n"
	@printf "  make setup             Install project dependencies\n"
	@printf "  make test              Run all local tests and type checks\n"
	@printf "  make check             Alias for make test\n"
	@printf "  make api-test          Run backend pytest suite\n"
	@printf "  make api-typecheck     Run backend Pyright check\n"
	@printf "  make web-typecheck     Run web TypeScript check\n"
	@printf "  make api-smoke         Check running API health and pipeline routes\n"
	@printf "  make compose-up        Start the full local stack\n"
	@printf "  make compose-debug     Start the full stack with debug ports\n"
	@printf "  make compose-debug-api Start only API/Postgres/Redis with debug ports\n"
	@printf "  make compose-down      Stop the local stack\n"
	@printf "  make compose-logs      Follow Docker Compose logs\n"

setup:
	mise run setup

test: compose-config api-typecheck api-test web-typecheck

check: test

compose-config:
	docker compose config --quiet

api-typecheck:
	pnpm api:typecheck

api-test:
	cd backend && uv run pytest

web-typecheck:
	pnpm --filter @repolm/web typecheck

api-smoke:
	curl -fsS http://localhost:8000/health
	curl -fsS http://localhost:8000/pipeline

compose-up:
	docker compose up --build

compose-debug:
	docker compose -f compose.yaml -f compose.debug.yaml up --build

compose-debug-api:
	docker compose -f compose.yaml -f compose.debug.yaml up --build api postgres redis

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f
