from app.pipeline import (
    PIPELINE_STAGES,
    PIPELINE_STAGE_IDS,
    STAGE_APPROVAL,
    STAGE_REPO_SYNC,
    STAGE_STATUS_DONE,
    WORKER_STAGE_IDS,
    build_done_stage_results,
)


def test_pipeline_stages_preserve_stage_order() -> None:
    assert [stage.id for stage in PIPELINE_STAGES] == list(PIPELINE_STAGE_IDS)
    assert len(PIPELINE_STAGES) == len({stage.id for stage in PIPELINE_STAGES})


def test_worker_stage_ids_exclude_human_approval() -> None:
    assert STAGE_APPROVAL not in WORKER_STAGE_IDS
    assert set(WORKER_STAGE_IDS) == set(PIPELINE_STAGE_IDS) - {STAGE_APPROVAL}


def test_build_done_stage_results_uses_pipeline_order() -> None:
    details = {stage_id: f"detail:{stage_id}" for stage_id in PIPELINE_STAGE_IDS}

    results = build_done_stage_results(details)

    assert [result.id for result in results] == list(PIPELINE_STAGE_IDS)
    assert [result.status for result in results] == [STAGE_STATUS_DONE] * len(
        PIPELINE_STAGE_IDS
    )
    assert results[0].detail == f"detail:{STAGE_REPO_SYNC}"
