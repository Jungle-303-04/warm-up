-- repo-rag Postgres 확장 및 인덱스
-- 테이블 자체는 SQLAlchemy Base.metadata.create_all 로 생성한다.
-- 이 파일은 create_all 이후에 실행한다.

CREATE EXTENSION IF NOT EXISTS vector;

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
