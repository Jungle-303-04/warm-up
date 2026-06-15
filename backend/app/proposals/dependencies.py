"""제안 리뷰 의존성 배선.

in-memory 저장소는 프로세스 단일 인스턴스로 유지(lru_cache)해 요청 간 상태를 보존한다.
파이프라인은 Phase 1의 LLM 제안 배선(build_llm_proposer)을 그대로 재사용한다.
"""

from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.pipeline.application.service import PipelineService
from app.pipeline.dependencies import build_llm_proposer
from app.pipeline.domain.agent import AgentProposalService
from app.proposals.application.service import ProposalReviewService
from app.proposals.infrastructure.in_memory_store import InMemoryProposalStore


@lru_cache(maxsize=1)
def _store() -> InMemoryProposalStore:
    return InMemoryProposalStore()


def get_proposal_review_service(
    settings: Settings = Depends(get_settings),
) -> ProposalReviewService:
    pipeline = PipelineService(agent=AgentProposalService(proposer=build_llm_proposer(settings)))
    return ProposalReviewService(store=_store(), pipeline=pipeline)
