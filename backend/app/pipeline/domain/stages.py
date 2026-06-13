from dataclasses import dataclass
from typing import Mapping

from app.pipeline.api.schemas import StageResult
from app.pipeline.domain.constants import (
    STAGE_AGENT_PROPOSAL,
    STAGE_APPROVAL,
    STAGE_CODE_INDEX,
    STAGE_RAG_INDEX,
    STAGE_REPO_SYNC,
    STAGE_STATUS_DONE,
)


@dataclass(frozen=True)
class PipelineStage:
    id: str
    name: str
    purpose: str


PIPELINE_STAGES: tuple[PipelineStage, ...] = (
    PipelineStage(
        id=STAGE_REPO_SYNC,
        name="저장소 동기화",
        purpose="요청 파일 또는 원격 Git 저장소를 읽어 저장소 스냅샷을 만든다.",
    ),
    PipelineStage(
        id=STAGE_CODE_INDEX,
        name="코드 인덱싱",
        purpose="스냅샷 파일에서 함수와 파일 단위 참조 정보를 추출한다.",
    ),
    PipelineStage(
        id=STAGE_RAG_INDEX,
        name="RAG 인덱싱",
        purpose="참조된 파일 내용을 검색과 근거 제시에 사용할 텍스트 조각으로 만든다.",
    ),
    PipelineStage(
        id=STAGE_AGENT_PROPOSAL,
        name="에이전트 제안",
        purpose="코드 참조와 검색 조각을 근거로 사용자가 검토할 제안을 만든다.",
    ),
    PipelineStage(
        id=STAGE_APPROVAL,
        name="승인 처리",
        purpose="생성된 제안을 승인 상태로 바꾸어 다음 단계에서 사용할 수 있게 한다.",
    ),
)

PIPELINE_STAGE_IDS: tuple[str, ...] = tuple(stage.id for stage in PIPELINE_STAGES)
WORKER_STAGE_IDS: tuple[str, ...] = tuple(
    stage.id for stage in PIPELINE_STAGES if stage.id != STAGE_APPROVAL
)


def build_done_stage_results(details: Mapping[str, str]) -> list[StageResult]:
    return [
        StageResult(id=stage_id, status=STAGE_STATUS_DONE, detail=details[stage_id])
        for stage_id in PIPELINE_STAGE_IDS
    ]
