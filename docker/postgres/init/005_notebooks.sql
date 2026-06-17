-- 노트북 스키마 — app/notebooks/infrastructure/models.py 의 ORM 과 1:1 일치.
-- repo 소스의 repo_snapshot([{path, content} ...]) 은 JSONB 로 저장한다.
-- notebook_sources 는 notebook_id FK(ON DELETE CASCADE) 로 노트북에 종속된다.

CREATE TABLE IF NOT EXISTS notebooks (
    id text PRIMARY KEY,
    owner_user_id bigint,
    title text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE notebooks ADD COLUMN IF NOT EXISTS owner_user_id bigint;
ALTER TABLE notebooks DROP COLUMN IF EXISTS summary;

CREATE INDEX IF NOT EXISTS notebooks_owner_user_id_idx
ON notebooks(owner_user_id);

CREATE TABLE IF NOT EXISTS notebook_sources (
    id text PRIMARY KEY,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    kind text NOT NULL,
    title text NOT NULL,
    content text,
    url text,
    repository_url text,
    branch text,
    content_hash text,
    derived_from_artifact_id text,
    lineage_source_ids jsonb,
    repo_commits jsonb,
    repo_snapshot jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE notebook_sources ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE notebook_sources ADD COLUMN IF NOT EXISTS derived_from_artifact_id text;
ALTER TABLE notebook_sources ADD COLUMN IF NOT EXISTS lineage_source_ids jsonb;
ALTER TABLE notebook_sources ADD COLUMN IF NOT EXISTS repo_commits jsonb;

CREATE INDEX IF NOT EXISTS notebook_sources_notebook_id_idx
ON notebook_sources(notebook_id);

CREATE TABLE IF NOT EXISTS notebook_chat_messages (
    id text PRIMARY KEY,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    role text NOT NULL,
    content text NOT NULL,
    citations jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_ids jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notebook_chat_messages_notebook_id_idx
ON notebook_chat_messages(notebook_id);
