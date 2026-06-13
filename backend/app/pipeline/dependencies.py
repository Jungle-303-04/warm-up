from app.pipeline.application.service import PipelineService


def get_pipeline_service() -> PipelineService:
    return PipelineService()
