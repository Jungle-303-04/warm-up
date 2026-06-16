-- 산출물(다이어그램/요약/메모) 테이블.
-- app/notebooks/infrastructure/models.py 의 ArtifactModel 과 1:1.
-- source_ids 는 생성 기준 소스 id 배열(note 는 빈 배열) → JSONB.
-- notebook_id FK(ON DELETE CASCADE)로 노트북에 종속된다.

CREATE TABLE IF NOT EXISTS notebook_artifacts (
    id text PRIMARY KEY,
    notebook_id text NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    type text NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    source_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_notebook_artifacts_notebook_id
ON notebook_artifacts (notebook_id);
