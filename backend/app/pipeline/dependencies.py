from app.pipeline.service import PipelineService


def get_pipeline_service() -> PipelineService:
    return PipelineService()
