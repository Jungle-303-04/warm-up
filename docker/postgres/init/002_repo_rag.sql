CREATE TABLE IF NOT EXISTS repositories (
    id uuid PRIMARY KEY,
    source_key text NOT NULL,
    name text NOT NULL,
    branch text NOT NULL,
    repository_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (source_key)
);

CREATE TABLE IF NOT EXISTS repo_snapshots (
    id uuid PRIMARY KEY,
    repository_id uuid NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    branch text NOT NULL,
    commit_sha text NOT NULL,
    file_count integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS repo_files (
    id uuid PRIMARY KEY,
    repository_id uuid NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    snapshot_id uuid NOT NULL REFERENCES repo_snapshots(id) ON DELETE CASCADE,
    path text NOT NULL,
    content_hash text NOT NULL,
    status text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS repo_files_one_active_path_idx
ON repo_files(repository_id, path)
WHERE is_active = true AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS repo_files_deleted_at_idx
ON repo_files(deleted_at)
WHERE deleted_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS retrieval_chunks (
    id text PRIMARY KEY,
    repository_id uuid NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_id uuid NOT NULL REFERENCES repo_files(id) ON DELETE CASCADE,
    snapshot_id uuid NOT NULL REFERENCES repo_snapshots(id) ON DELETE CASCADE,
    source_path text NOT NULL,
    chunk_hash text NOT NULL,
    text text NOT NULL,
    citation text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS retrieval_chunks_active_hash_idx
ON retrieval_chunks(repository_id, chunk_hash)
WHERE is_active = true AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS retrieval_chunks_deleted_at_idx
ON retrieval_chunks(deleted_at)
WHERE deleted_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS sync_jobs (
    id uuid PRIMARY KEY,
    repository_id uuid REFERENCES repositories(id) ON DELETE SET NULL,
    trigger_type text NOT NULL,
    branch text NOT NULL,
    requested_commit_sha text,
    idempotency_key text NOT NULL,
    lock_key text NOT NULL,
    status text NOT NULL,
    request_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS sync_jobs_one_active_idempotency_idx
ON sync_jobs(trigger_type, idempotency_key)
WHERE status IN ('queued', 'running');

CREATE UNIQUE INDEX IF NOT EXISTS sync_jobs_one_active_lock_idx
ON sync_jobs(lock_key)
WHERE status IN ('queued', 'running');

CREATE TABLE IF NOT EXISTS sync_events (
    id uuid PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES sync_jobs(id) ON DELETE CASCADE,
    stage text NOT NULL,
    detail text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sync_events_job_created_idx
ON sync_events(job_id, created_at);
