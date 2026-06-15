CREATE TABLE IF NOT EXISTS github_tokens (
    user_id bigint PRIMARY KEY,
    access_token text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
