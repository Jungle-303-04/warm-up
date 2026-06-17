"""제안 리뷰 의존성 배선.

POSTGRES_DATABASE_URL이 있으면 SQL 저장소로 영속화하고, 없으면 in-memory로 동작한다.
저장소는 프로세스 단일 인스턴스로 유지(lru_cache)한다. 파이프라인은 Phase 1의
LLM 제안 배선(build_llm_proposer)을 그대로 재사용한다.
"""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.pipeline.service import PipelineService
from app.pipeline.dependencies import build_llm_proposer
from app.pipeline.domain import AgentProposalService
from app.proposals.ports import ProposalStore
from app.proposals.stores import InMemoryProposalStore


@lru_cache(maxsize=1)
def _in_memory_store() -> InMemoryProposalStore:
    return InMemoryProposalStore()


@lru_cache(maxsize=1)
def _sql_store() -> ProposalStore:
    settings = get_settings()
    if settings.postgres_database_url is None:
        raise RuntimeError("POSTGRES_DATABASE_URL is required for SQL storage")

    from app.proposals.stores import SqlProposalStore
    from app.repo_rag.infrastructure.db import get_shared_session_factory

    session_factory = get_shared_session_factory(settings.postgres_database_url)
    return SqlProposalStore(session_factory)



def get_proposal_store(settings: Settings = Depends(get_settings)) -> ProposalStore:
    return _sql_store() if settings.uses_postgres else _in_memory_store()


def get_pipeline_service(
    settings: Settings = Depends(get_settings),
) -> PipelineService:
    return PipelineService(agent=AgentProposalService(proposer=build_llm_proposer(settings)))
