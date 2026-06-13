from app.pipeline import PIPELINE_STAGE_IDS
from app.pipeline.api.schemas import PipelineRequest, RepoFile
from app.pipeline.application.service import PipelineService
from app.pipeline.domain.constants import PROPOSAL_STATUS_APPROVED


def test_run_orchestrates_all_minimum_pipeline_stages() -> None:
    service = PipelineService()

    response = service.run(
        PipelineRequest(
            files=[
                RepoFile(
                    path="backend/app/api/auth.py",
                    content="def login(user_id: str) -> str:\n    return f'token:{user_id}'\n",
                ),
                RepoFile(
                    path="docs/auth.md",
                    content="# Auth\n\nLogin issues a token for the current user.\n",
                ),
            ]
        )
    )

    assert response.repository.repository == "sample-repo"
    assert response.code_references
    assert response.retrieval_chunks
    assert response.proposals[0].status == PROPOSAL_STATUS_APPROVED
    assert [stage.id for stage in response.stages] == list(PIPELINE_STAGE_IDS)
