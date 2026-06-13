from enum import StrEnum


DEFAULT_REPOSITORY = "sample-repo"
DEFAULT_BRANCH = "main"

STAGE_REPO_SYNC = "repo-sync"
STAGE_CODE_INDEX = "code-index"
STAGE_RAG_INDEX = "rag-index"
STAGE_AGENT_PROPOSAL = "agent-proposal"
STAGE_APPROVAL = "approval"

STAGE_STATUS_DONE = "done"

CODE_REFERENCE_STATUS_VERIFIED = "verified"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"


class ProposalType(StrEnum):
    RELATED_CODE_SUGGESTION = "related_code_suggestion"
