from app.pipeline import PIPELINE_STAGE_IDS
from app.pipeline.api.schemas import PipelineRequest
from app.pipeline.application.service import PipelineService


def test_run_orchestrates_all_minimum_pipeline_stages() -> None:
    service = PipelineService()

    response = service.run(PipelineRequest())

    assert response.repository.repository == "sample-repo"
    assert response.code_references
    assert response.retrieval_chunks
    assert response.proposals[0].status == "approved"
    assert response.publish_snapshot.status == "published"
    assert [stage.id for stage in response.stages] == list(PIPELINE_STAGE_IDS)
