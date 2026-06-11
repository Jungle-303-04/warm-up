# 2026-06-11 Warm-up Backend CRUD Analysis

## Scope

- Person: [Gain](./README.md)
- Repository: [`Jungle-303-04/warm-up`](https://github.com/Jungle-303-04/warm-up)
- Branch: [`gain`](https://github.com/Jungle-303-04/warm-up/tree/gain)
- Author: `ummfieg <ummfieg@naver.com>`
- Latest inspected commit: [`ebbef70`](https://github.com/Jungle-303-04/warm-up/commit/ebbef7056201317e144e8acc1f336754ef272f3a)
- Commit message: `chore: crud api 의사코드 작성`
- Captured at: `2026-06-11 01:34:10 +0900`

## What Was Implemented

Gain implemented the early full-stack skeleton for an AI font recommendation app.

- Frontend: React + Vite app with a brand-description input, recommendation button, and `/health` backend call.
- Backend: FastAPI app with `/`, `/health`, CORS for `localhost:5173`, and `/posts` routes.
- Database connection: `.env` based `DATABASE_URL` loading and SQLModel engine creation.
- Database initialization: `init_db.py` imports models and calls `SQLModel.metadata.create_all(engine)`.
- Models:
  - `Font`: font metadata such as name, source, license, category, tags, description, weights, webfont URL, and source URL.
  - `User`: nickname, password hash, and creation timestamp.
  - `Post`: title, content, `font_id`, `user_id`, creation timestamp, and update timestamp.
- API progress:
  - `GET /posts` already opens a DB session and returns `select(Post).all()`.
  - `POST /posts`, `GET /posts/{post_id}`, `PUT /posts/{post_id}`, and `DELETE /posts/{post_id}` are currently pseudocode placeholders.

## What Gain Considered

The comments show that Gain is thinking beyond table creation:

- The post list should probably return only display-oriented data such as title, font preview, and font tags.
- The create endpoint should return data that helps the frontend navigate to a detail page or update a list immediately.
- Backend validation is needed even if the frontend already validates input.
- Posts should be connected to both fonts and users.
- Concurrency came up as a concern during post creation.

## What Went Well

- The implementation order is healthy: connectivity check, DB connection, table modeling, then API design.
- The data model already captures key relationships through `font_id` and `user_id`.
- The comments are useful planning notes, not just noise. They expose the intended API behavior.
- `GET /posts` is a good first slice because it proves FastAPI, SQLModel sessions, and table selection can work together.

## What Is Weak Or Risky

- Most CRUD routes are not implemented yet and return empty placeholder responses.
- Request and response schemas are not separated from table models.
- `database.py` connects and prints during import, which can create side effects during tests and server startup.
- Backend dependencies and setup instructions are not visible yet, so teammates may struggle to run the service.
- `updated_at` has an initial default but no update logic when a post changes.
- `tags` and `weights` are stored as plain text. That is acceptable for a first pass, but weak for filtering and search.
- The code comments still say user information is not table-created, but `User` now exists. This is a small stale-comment signal.

## How To Improve

The immediate improvement path should stay small:

1. Add API schemas:
   - `PostCreate`
   - `PostRead`
   - `PostUpdate`
2. Implement one CRUD route at a time:
   - Start with `POST /posts`.
   - Then `GET /posts/{post_id}` with 404 handling.
   - Then `PUT /posts/{post_id}` with `updated_at` refresh.
   - Then `DELETE /posts/{post_id}`.
3. Keep authentication out of scope for now:
   - Use a temporary `user_id` input or seed user.
   - Do not let login/password work block CRUD learning.
4. Move DB connection verification out of import-time module code.
5. Add a backend setup note:
   - dependencies
   - `.env.example`
   - DB initialization command
   - server run command
6. Decide whether post list responses should include expanded font fields.

## Likely Blockers

- Gain may be overthinking concurrency before basic CRUD is complete.
- API request/response shape is still undecided.
- User/auth scope may be unclear.
- Database setup may be locally understood but not reproducible for teammates.

## What The User Can Say Or Do

The most useful intervention is to reduce uncertainty:

- Tell Gain: "Concurrency can wait. Finish basic CRUD first."
- Define the first `POST /posts` request body together.
- Decide whether login is in scope now or deferred.
- Provide 2-3 sample font rows and 1 sample post flow.
- Ask Gain to document the exact backend run steps after CRUD works once.

## Vault Linking Decision

The vault operator decision is to reuse the existing vault layout instead of
creating a new top-level `people/` folder.

Vault-side locations:

- Person node: `/Users/woonyong/workspace/vault/wiki/common/person-lim-gain.md`
- Project node: `/Users/woonyong/workspace/vault/wiki/career/project-warm-up.md`
- Person-project analysis: `/Users/woonyong/workspace/vault/wiki/career/project-warm-up-lim-gain-analysis.md`

Obsidian-style link model:

- `[[people-index|사람 관계 인덱스]] -> [[person-lim-gain|임가인]]`
- `[[portfolio-project-moc|팀 프로젝트]] -> [[project-warm-up|warm-up 프로젝트]]`
- `[[project-warm-up|warm-up 프로젝트]] -> [[project-warm-up-lim-gain-analysis|임가인 warm-up 작업 분석]]`

Operational rule:

- Person records stay in `wiki/common/person-*.md`.
- Project summaries and person-specific project analysis stay in `wiki/career/`.
- Analysis documents must keep `analysis_date`, `branch_head_sha`, repo URL, branch URL, and author identity.
- These documents remain `access: private` because they can contain emails and evaluative notes.
