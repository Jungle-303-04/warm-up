from app.pipeline import (
    ALL,
    APPROVAL,
    DONE,
    IDS,
    REPO_SYNC,
    WORKER_IDS,
    build_done_stage_results,
)


def test_pipeline_stages_preserve_stage_order() -> None:
    assert [stage.id for stage in ALL] == list(IDS)
    assert len(ALL) == len({stage.id for stage in ALL})


def test_worker_stage_ids_exclude_human_approval() -> None:
    assert APPROVAL not in WORKER_IDS
    assert set(WORKER_IDS) == set(IDS) - {APPROVAL}


def test_build_done_stage_results_uses_pipeline_order() -> None:
    details = {stage_id: f"detail:{stage_id}" for stage_id in IDS}

    results = build_done_stage_results(details)

    assert [result.id for result in results] == list(IDS)
    assert [result.status for result in results] == [DONE] * len(
        IDS
    )
    assert results[0].detail == f"detail:{REPO_SYNC}"
