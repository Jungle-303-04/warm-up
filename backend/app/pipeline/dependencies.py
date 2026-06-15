"""파이프라인 의존성 배선.

llm_provider가 "none"이면 LLM 없이 휴리스틱 제안으로 동작하고,
실제 제공자가 지정되면 LangGraph 제안 그래프를 조립해 에이전트에 주입한다.
infra import는 지연시켜 LLM 패키지가 없어도 기본 경로가 깨지지 않게 한다.
"""

from fastapi import Depends

from app.config import Settings, get_settings
from app.pipeline.application.service import PipelineService
from app.pipeline.domain.agent import AgentProposalService
from app.pipeline.domain.proposer import LlmProposer


def build_llm_proposer(settings: Settings) -> LlmProposer | None:
    if settings.llm_provider == "none":
        return None

    from app.pipeline.infrastructure.chat_models import build_chat_model
    from app.pipeline.infrastructure.langgraph_proposer import LangGraphProposer

    chat_model = build_chat_model(
        settings.llm_provider,
        settings.llm_model,
        settings.openai_api_key,
    )
    return LangGraphProposer(chat_model=chat_model)


def get_pipeline_service(
    settings: Settings = Depends(get_settings),
) -> PipelineService:
    agent = AgentProposalService(proposer=build_llm_proposer(settings))
    return PipelineService(agent=agent)
