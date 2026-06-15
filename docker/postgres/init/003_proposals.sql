CREATE TABLE IF NOT EXISTS agent_proposals (
    id text PRIMARY KEY,
    repository text NOT NULL,
    target_path text NOT NULL,
    type text NOT NULL,
    proposed_change text NOT NULL,
    evidence jsonb NOT NULL DEFAULT '[]'::jsonb,
    confidence double precision NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    decided_at timestamptz,
    decided_reason text
);

CREATE INDEX IF NOT EXISTS agent_proposals_repository_idx
ON agent_proposals(repository);

CREATE INDEX IF NOT EXISTS agent_proposals_status_idx
ON agent_proposals(status);
