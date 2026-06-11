# 2026-06-11 Warm-up Board Model Analysis

## Scope

- Person: [Minjeong](./README.md)
- Repository: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- Branch: [`minjeong`](https://github.com/Jungle-303-04/warm-up/tree/minjeong)
- Author: `minmings111 <minmings111@gmail.com>`
- Latest inspected commit: [`09b3578`](https://github.com/Jungle-303-04/warm-up/commit/09b357825dd02c758c80c5f16b37616dfb11415b)
- Commit message: `chore: update backend requirements`
- Captured at: `2026-06-11 11:01:46 +09:00`
- Visual companion: [Board Class UML](./class-uml.md)

## Daily Summary

Minjeong moved the `board` domain from a commented layer scaffold into concrete
SQLAlchemy table modeling. The work shows a clear attempt to model board subtypes
and board-related users before writing the API surface.

The latest commit also updates backend dependencies and adds `SQLAlchemy`, which
removes one obvious environment blocker from the earlier model work.

## Pre-Day Context

### 2026-06-10 23:10 - `c681267 feat: add SQLAlchemy base mixins`

- Added `backend/app/db/base.py`.
- Created `Base` through SQLAlchemy `DeclarativeBase`.
- Added `TimestampMixin` with `created_at` and `updated_at`.
- Added `IdMixin` with an autoincrement integer primary key.
- Left a commented `UserInfo` stub, which later became cleanup work.

This was the turning point from plain FastAPI scaffold toward database-backed
domain modeling.

## Hourly Timeline

### 03:49 - `1c202b5 feat: define board SQLAlchemy models`

Implemented the first board-domain SQLAlchemy model set:

- `Board`
  - `board_type`
  - `title`
  - `content`
  - optional `tag`
  - `user_id` foreign key to `user.id`
- `ScheduleBoardDetail`
  - one row per board through primary-key `board_id`
  - `start_at`, `end_at`, and `importance`
  - DB check constraint for `importance` between 1 and 10
- `ProceedingsBoardDetail`
  - one row per board through primary-key `board_id`
  - `meeting_date`
- `BoardCarbonCopy`, `BoardAssignee`, `BoardParticipant`
  - join tables with composite primary keys `(board_id, user_id)`

What this suggests:

- Minjeong is thinking in terms of one common board table plus subtype detail
  tables, rather than one wide board table.
- She separated user participation roles into join tables, which leaves room for
  many users per board and multiple role categories.
- She started adding database constraints instead of relying only on application
  validation.

### 04:11 - `0f5fd69 feat: add schedule board task model`

Added `ScheduleBoardTask`:

- `id` from `IdMixin`
- `board_id` foreign key to `board.id`
- `task_name`
- `task_status`
- check constraint for `task_status` between 1 and 4

What this suggests:

- A schedule board is not just a date range. It can contain multiple actionable
  tasks.
- The comments map task status values to `Todo`, `In_progress`, `Done`, and
  `Blocked`.
- Minjeong is beginning to express workflow state in the database model.

### 04:12 - `bc58a39 chore: remove unused user info stub`

Removed the commented `UserInfo` stub from `backend/app/db/base.py`.

What this suggests:

- She noticed dead/commented modeling code and cleaned it up quickly.
- This keeps `base.py` focused on shared ORM infrastructure instead of a partial
  user table design.

### 11:01 - `09b3578 chore: update backend requirements`

Replaced the minimal backend requirements with pinned dependency versions,
including:

- `fastapi==0.136.3`
- `SQLAlchemy==2.0.50`
- `pydantic==2.13.4`
- `python-dotenv==1.2.2`
- `uvicorn==0.49.0`
- server runtime helpers such as `httptools`, `uvloop`, `watchfiles`, and
  `websockets`

What this fixes:

- The SQLAlchemy model code now has a declared package dependency.
- The backend environment is more reproducible than the previous two-line
  requirements file.

Remaining concern:

- There is still no declared database driver such as `psycopg`, `psycopg2`, or
  `asyncpg`.
- The requirements look like a full freeze, not a hand-curated minimal backend
  dependency list. That can be acceptable short-term, but it may make future
  dependency review noisier.

## What Was Implemented

- SQLAlchemy declarative base and reusable mixins.
- Board table with title/content/tag/user ownership fields.
- Schedule detail table with time range and importance constraint.
- Schedule task table with task status constraint.
- Proceedings detail table with meeting date.
- Three board-user role join tables:
  - carbon copy
  - assignee
  - participant
- Backend requirements with pinned versions and SQLAlchemy included.

## What Minjeong Appears To Have Considered

- A board can have different domain types, currently represented by integer
  `board_type`.
- Schedule boards need specialized fields that do not belong on every board.
- Proceedings boards need their own meeting date detail.
- Users can relate to a board in different roles, so role-specific join tables
  were chosen instead of one generic participant table.
- Some values should be constrained at the database layer, especially
  `importance` and `task_status`.
- Common columns should be centralized through mixins rather than repeated in
  every table.

## What Went Well

- The implementation is moving in a sensible order: base ORM infrastructure,
  domain models, task model, cleanup, then dependencies.
- SQLAlchemy 2 style typing with `Mapped` and `mapped_column` is a strong choice.
- `IdMixin` and `TimestampMixin` reduce duplication and show reusable design
  thinking.
- Composite primary keys on board-user join tables are appropriate for preventing
  duplicate role assignments.
- The cleanup commit shows good local hygiene after experimenting.
- Adding `SQLAlchemy` to `requirements.txt` addresses a real run/setup blocker.

## What Is Weak Or Risky

- `backend/app/main.py` imports `router` from `backend/app/domains/board/router.py`,
  but `router.py` still does not define an `APIRouter` instance. The app can fail
  before any model logic is usable.
- `ForeignKey("user.id")` is used, but no `User` ORM model or `user` table exists
  on `origin/minjeong`.
- No SQLAlchemy `relationship()` fields are defined, so navigation between board,
  detail, task, and user-role tables is still manual.
- There is no database engine/session module yet.
- There is no Alembic or other migration path.
- `board_type` and `task_status` are magic integers. They need enum-like names to
  avoid accidental misuse.
- The schedule model constrains `importance`, but it does not constrain
  `end_at >= start_at`.
- Timestamps use `datetime.utcnow`, which produces timezone-naive values.
- DTOs, service logic, and repository logic are still comments/placeholders.

## How To Improve Next

1. Make the app boot first.
   - Add `from fastapi import APIRouter`.
   - Add `router = APIRouter()` in `backend/app/domains/board/router.py`.
   - Add one temporary `GET /boards/` endpoint returning an empty list.
2. Define the missing user dependency.
   - Either implement a minimal `User` model or temporarily remove/replace user
     foreign keys until user scope is decided.
3. Add database connection infrastructure.
   - Create engine/session handling.
   - Add `.env.example` for the database URL.
   - Choose a migration strategy.
4. Replace magic integers.
   - Define `BoardType` and `TaskStatus` enums or constants.
   - Keep DB constraints aligned with those values.
5. Add relationships after table shape stabilizes.
   - `Board.schedule_detail`
   - `Board.proceedings_detail`
   - `Board.tasks`
   - role join table relationships to `User`
6. Implement one vertical slice.
   - `BoardCreate`
   - `BoardRead`
   - repository create/list
   - service create/list
   - router create/list

## Likely Blockers

- Minjeong may be designing the table structure before confirming the minimal API
  slice that needs to run first.
- User/auth ownership is unresolved and currently leaks into multiple foreign
  keys.
- The backend can still be blocked at import time because `router.py` has no
  exported `router`.
- The project has model definitions but no persistence runtime path yet:
  no session dependency, no migration, no request/response schema, no repository.

## What The User Can Say Or Do

- Tell Minjeong: "Good model direction. Now make the backend boot with the
  smallest board router before adding more tables."
- Ask her to decide whether `User` is in scope today. If not, use a temporary
  placeholder strategy explicitly.
- Give her a concrete first API target:
  - `GET /boards/` returns `[]`
  - `POST /boards/` creates only the base `Board`
  - schedule/proceedings details can come after that
- Ask her to name `board_type` and `task_status` values as constants or enums
  before more business logic depends on them.
- Ask for a short backend run note after the router boots once.

## Current Visual State

The current class-level view is documented in [Board Class UML](./class-uml.md).
That diagram intentionally reflects the implemented SQLAlchemy classes, not the
future router/service/repository plan.
