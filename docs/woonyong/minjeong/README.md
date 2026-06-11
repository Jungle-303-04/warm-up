# Minjeong

This folder tracks Minjeong's branch-level implementation notes and visual design snapshots.

## Current Snapshot

- Repository: `Jungle-303-04/warm-up`
- Branch: `minjeong`
- Latest inspected commit: `3d79dd0 feat: scaffold board domain structure`
- Captured at: `2026-06-10 11:07:40 +09:00`

## Visual Notes

- [Board Class UML](./class-uml.md)

## Implementation Reading

The latest implementation creates the `board` backend domain boundary:

- `backend/app/domains/board/model.py`
- `backend/app/domains/board/repository.py`
- `backend/app/domains/board/router.py`
- `backend/app/domains/board/schema.py`
- `backend/app/domains/board/service.py`
- `backend/app/main.py`

The current code is a scaffold. The important design direction is already visible:
FastAPI routes should receive board requests, pass work to a service layer, and let
the repository layer handle database access through a SQLAlchemy model.

