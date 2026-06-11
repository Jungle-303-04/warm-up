# Minjeong

This folder tracks Minjeong's branch-level implementation notes, daily work
archives, and visual class-level design snapshots.

## Current Snapshot

- Repository: `Jungle-303-04/warm-up`
- Branch: `minjeong`
- Author: `minmings111 <minmings111@gmail.com>`
- Latest inspected commit: `09b3578 chore: update backend requirements`
- Captured at: `2026-06-11 11:01:46 +09:00`

## Archive

- [2026-06-11 Warm-up Board Model Analysis](./2026-06-11-warm-up-board-model-analysis.md)

## Visual Notes

- [Board Class UML](./class-uml.md) - Mermaid class diagram for the implemented SQLAlchemy models.

## Implementation Reading

The latest implementation has moved beyond the initial scaffold into SQLAlchemy
modeling for the board domain:

- `backend/app/db/base.py`
- `backend/app/domains/board/model.py`
- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/schema.py`
- `backend/app/domains/board/service.py`

The main design direction is a layered FastAPI backend:

- `router.py` receives board HTTP requests.
- `service.py` should contain business workflow logic.
- `repository.py` should isolate SQLAlchemy persistence.
- `schema.py` should define Pydantic request and response DTOs.
- `model.py` now defines the table structure for board records, schedule details,
  proceedings details, tasks, and board-user role join tables.

The current branch still needs an executable router, database session setup,
schema/service/repository implementation, and a concrete `User` model before the
board domain can run end to end.
