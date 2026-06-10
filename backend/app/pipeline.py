from dataclasses import asdict, dataclass
from typing import Mapping

from app.schemas.pipeline import StageResult


@dataclass(frozen=True)
class PipelineStage:
    id: str
    name: str
    purpose: str


PIPELINE_STAGES: tuple[PipelineStage, ...] = (
    PipelineStage(
        id="repo-sync",
        name="Repo Sync",
        purpose="Import repositories, issues, PRs, labels, milestones, and permissions.",
    ),
    PipelineStage(
        id="code-index",
        name="Code Index",
        purpose="Extract file, symbol, commit, and code reference metadata.",
    ),
    PipelineStage(
        id="rag-index",
        name="RAG Index",
        purpose="Build retrieval chunks for docs, issues, PRs, and code with permission metadata.",
    ),
    PipelineStage(
        id="agent-proposal",
        name="Agent Proposal",
        purpose="Create evidence-backed suggestions without direct write actions.",
    ),
    PipelineStage(
        id="approval",
        name="Approval",
        purpose="Approve safe proposals before publishing or write actions.",
    ),
    PipelineStage(
        id="static-publish",
        name="Static Publish",
        purpose="Render a read-only project archive with search, filters, and link status.",
    ),
)

PIPELINE_STAGE_IDS: tuple[str, ...] = tuple(stage.id for stage in PIPELINE_STAGES)
WORKER_STAGE_IDS: tuple[str, ...] = tuple(
    stage.id for stage in PIPELINE_STAGES if stage.id != "approval"
)


def pipeline_stage_payloads() -> list[dict[str, str]]:
    return [asdict(stage) for stage in PIPELINE_STAGES]


def build_done_stage_results(details: Mapping[str, str]) -> list[StageResult]:
    return [
        StageResult(id=stage_id, status="done", detail=details[stage_id])
        for stage_id in PIPELINE_STAGE_IDS
    ]
