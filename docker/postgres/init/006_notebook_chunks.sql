-- notebooks 도메인 추가 테이블: 채팅 메시지 + RAG 청크.
-- app/notebooks/infrastructure/models.py 의 모델과 1:1.
-- 임베딩 차원 1536, 전문검색 config 'simple'(기본 설정) 기준.
-- vector 확장은 001_extensions.sql 에서 먼저 생성된다.

-- 채팅 메시지(대화 영속화)
CREATE TABLE IF NOT EXISTS notebook_chat_messages (
    id text PRIMARY KEY,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    role text NOT NULL,
    content text NOT NULL,
    citations jsonb NOT NULL DEFAULT '[]'::jsonb,
    source_ids jsonb,
    created_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_notebook_chat_messages_notebook_id
ON notebook_chat_messages (notebook_id);

CREATE TABLE IF NOT EXISTS notebook_chunks (
    id text PRIMARY KEY,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    source_id text NOT NULL REFERENCES notebook_sources(id) ON DELETE CASCADE,
    file_path text,
    chunk_index integer NOT NULL,
    language text,
    format text,
    heading_path jsonb,
    page integer,
    start_line integer,
    end_line integer,
    start_offset integer,
    end_offset integer,
    content_hash text,
    parent_chunk_id text,
    prev_chunk_id text,
    next_chunk_id text,
    text text NOT NULL,
    embedding vector(1536),
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
    created_at timestamptz NOT NULL
);

ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS format text;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS heading_path jsonb;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS page integer;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS start_line integer;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS end_line integer;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS start_offset integer;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS end_offset integer;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS content_hash text;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS parent_chunk_id text;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS prev_chunk_id text;
ALTER TABLE notebook_chunks ADD COLUMN IF NOT EXISTS next_chunk_id text;

CREATE INDEX IF NOT EXISTS ix_notebook_chunks_notebook_id ON notebook_chunks (notebook_id);
CREATE INDEX IF NOT EXISTS ix_notebook_chunks_source_id ON notebook_chunks (source_id);

-- 키워드(전문검색): content_tsv GIN
CREATE INDEX IF NOT EXISTS ix_notebook_chunks_content_tsv
ON notebook_chunks USING gin (content_tsv);

-- 벡터(의미검색): 코사인 거리 HNSW
CREATE INDEX IF NOT EXISTS ix_notebook_chunks_embedding_hnsw
ON notebook_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS notebook_index_progress (
    source_id text PRIMARY KEY REFERENCES notebook_sources(id) ON DELETE CASCADE,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    status text NOT NULL,
    total_files integer NOT NULL DEFAULT 0,
    processed_files integer NOT NULL DEFAULT 0,
    skipped_files integer NOT NULL DEFAULT 0,
    total_chunks integer NOT NULL DEFAULT 0,
    indexed_chunks integer NOT NULL DEFAULT 0,
    files jsonb NOT NULL DEFAULT '[]'::jsonb,
    error text,
    content_hash text,
    updated_at timestamptz NOT NULL DEFAULT now(),
    last_synced_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_notebook_index_progress_notebook_id
ON notebook_index_progress (notebook_id);
