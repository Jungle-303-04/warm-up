-- repo-rag 스키마 — app/repo_rag/infrastructure/models.py 의 ORM 과 1:1 일치.
-- 임베딩 차원/전문검색 config 는 기본 설정(embedding_dimension=1536,
-- search_text_config='simple') 기준이다. 설정을 바꾸면 이 파일도 함께 바꿔야 한다.
-- vector 확장은 001_extensions.sql 에서 먼저 생성된다.

CREATE TABLE IF NOT EXISTS repository_connections (
    id text PRIMARY KEY,
    source_key text NOT NULL UNIQUE,
    name text NOT NULL,
    branch text NOT NULL,
    repository_url text,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_repository_connections_source_key
ON repository_connections (source_key);

CREATE TABLE IF NOT EXISTS branch_snapshots (
    id text PRIMARY KEY,
    repository_id text NOT NULL REFERENCES repository_connections(id),
    branch text NOT NULL,
    commit_sha text NOT NULL,
    file_count integer NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_branch_snapshots_repository_id
ON branch_snapshots (repository_id);

CREATE TABLE IF NOT EXISTS source_files (
    id text PRIMARY KEY,
    repository_id text NOT NULL REFERENCES repository_connections(id),
    snapshot_id text NOT NULL REFERENCES branch_snapshots(id),
    path text NOT NULL,
    content_hash text NOT NULL,
    status text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    last_seen_at timestamptz NOT NULL,
    deleted_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_source_files_repository_id ON source_files (repository_id);
CREATE INDEX IF NOT EXISTS ix_source_files_path ON source_files (path);

CREATE TABLE IF NOT EXISTS source_chunks (
    id text PRIMARY KEY,
    repository_id text NOT NULL REFERENCES repository_connections(id),
    file_id text NOT NULL REFERENCES source_files(id),
    snapshot_id text NOT NULL REFERENCES branch_snapshots(id),
    source_path text NOT NULL,
    chunk_hash text NOT NULL,
    text text NOT NULL,
    citation text NOT NULL,
    chunk_type text,
    symbol_name text,
    start_line integer,
    end_line integer,
    language text,
    embedding vector(1536),
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL,
    deleted_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_source_chunks_repository_id ON source_chunks (repository_id);
CREATE INDEX IF NOT EXISTS ix_source_chunks_source_path ON source_chunks (source_path);

-- 키워드(전문검색): content_tsv 생성 컬럼에 GIN 인덱스
CREATE INDEX IF NOT EXISTS ix_source_chunks_content_tsv
ON source_chunks USING gin (content_tsv);

-- 벡터(의미검색): 코사인 거리 기준 HNSW 인덱스
CREATE INDEX IF NOT EXISTS ix_source_chunks_embedding_hnsw
ON source_chunks USING hnsw (embedding vector_cosine_ops);

-- active 청크 조회 가속용 부분 인덱스
CREATE INDEX IF NOT EXISTS ix_source_chunks_active
ON source_chunks (repository_id)
WHERE is_active;

CREATE TABLE IF NOT EXISTS sync_jobs (
    id text PRIMARY KEY,
    trigger_type text NOT NULL,
    branch text NOT NULL,
    idempotency_key text NOT NULL,
    lock_key text NOT NULL,
    repository_id text,
    requested_commit_sha text,
    status text NOT NULL DEFAULT 'queued',
    error text,
    request_json jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    started_at timestamptz,
    finished_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_sync_jobs_idempotency_key ON sync_jobs (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_sync_jobs_lock_key ON sync_jobs (lock_key);

CREATE TABLE IF NOT EXISTS sync_events (
    id text PRIMARY KEY,
    job_id text NOT NULL REFERENCES sync_jobs(id),
    stage text NOT NULL,
    detail text NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sync_events_job_id ON sync_events (job_id);
