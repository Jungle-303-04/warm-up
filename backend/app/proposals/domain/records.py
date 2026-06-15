"""제안(=퀘스트) 영속 레코드.

제안은 상태(PENDING → APPROVED/REJECTED)를 가지는 추적 대상이다.
누가 언제 왜 결정했는지(decided_*)를 함께 보관해 감사 이력을 남긴다.
"""

from dataclasses import dataclass
from datetime import datetime

from app.pipeline.api.schemas import ProposalStatus, ProposalType


@dataclass(slots=True)
class ProposalRecord:
    id: str
    repository: str
    target_path: str
    type: ProposalType
    proposed_change: str
    evidence: list[str]
    confidence: float
    status: ProposalStatus
    created_at: datetime
    decided_at: datetime | None = None
    decided_reason: str | None = None
