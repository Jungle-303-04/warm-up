PIPELINE_STAGES: list[dict[str, str]] = [
    {
        "id": "repo-sync",
        "name": "Repo Sync",
        "purpose": "Import repositories, issues, PRs, labels, milestones, and permissions.",
    },
    {
        "id": "code-index",
        "name": "Code Index",
        "purpose": "Extract file, symbol, commit, and code reference metadata.",
    },
    {
        "id": "rag-index",
        "name": "RAG Index",
        "purpose": "Build retrieval chunks for docs, issues, PRs, and code with permission metadata.",
    },
    {
        "id": "agent-proposal",
        "name": "Agent Proposal",
        "purpose": "Create evidence-backed suggestions without direct write actions.",
    },
    {
        "id": "approval",
        "name": "Approval",
        "purpose": "Approve safe proposals before publishing or write actions.",
    },
    {
        "id": "static-publish",
        "name": "Static Publish",
        "purpose": "Render a read-only project archive with search, filters, and link status.",
    },
]
