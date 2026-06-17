import re
from dataclasses import dataclass
from typing import Any

from app.agent.domain.chat import InferredRepositoryRef
from app.agent.service.agent_intent import (
    BASIS_MODE_ADD,
    BASIS_MODE_CLEAR,
    BASIS_MODE_REMOVE,
    BASIS_MODE_REPLACE,
    BasisMode,
    normalize_text,
)


REPOSITORY_ORDINAL_PATTERN = re.compile(r"(?<!\d)(\d+)\s*번\s*(?:레포|레포지토리|저장소)")
BRANCH_ORDINAL_PATTERN = re.compile(r"(?<!\d)(\d+)\s*번\s*(?:브랜치)?")
BARE_ORDINAL_PATTERN = re.compile(r"^\s*(\d+)\s*(?:번)?\s*$")
BRANCH_LIST_REPOSITORY_ORDINAL_PATTERN = re.compile(r"^\s*(\d+)\s*(?:번)?\s*브랜치")
PATH_SEPARATOR_PATTERN = re.compile(r"[\\/]+")
PATH_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_.-]+(?:[/\\][a-zA-Z0-9_.-]+)+")
KOREAN_PATH_SEGMENTS = {
    "백엔드": "backend",
    "프론트엔드": "frontend",
    "프론트": "frontend",
    "앱": "app",
    "어스": "auth",
    "인증": "auth",
}
MAX_COMPARISON_EVIDENCE_PATHS_PER_RUN = 16


@dataclass(frozen=True)
class SnapshotComparisonItem:
    """두 분석 run 사이의 파일 스냅샷 차이를 재사용 가능한 구조로 담는다."""

    base_run: Any
    compare_run: Any
    added_paths: list[str]
    removed_paths: list[str]
    changed_paths: list[str]


def resolve_runs_from_text(
    user_input: str,
    latest_runs: list[Any],
    current_refs: list[InferredRepositoryRef],
    messages: list[Any] | None = None,
    allow_repository_default: bool = True,
) -> list[Any]:
    """질문, 선택 기준, 이전 대화 맥락에서 레포/브랜치를 SQL run 후보에 매핑한다."""

    repository_names = find_repository_names_in_text(user_input, latest_runs)
    if not repository_names:
        repository_names = find_repository_names_by_ordinal(user_input, latest_runs)
    if not repository_names and len(unique_repository_names_from_refs(current_refs)) == 1:
        repository_names = unique_repository_names_from_refs(current_refs)
    if not repository_names:
        repository_names = find_recent_repository_names(messages or [], latest_runs)

    resolved_runs: list[Any] = []
    for repository_name in repository_names:
        resolved_runs.extend(
            resolve_runs_for_repository(
                user_input=user_input,
                latest_runs=latest_runs,
                repository_name=repository_name,
                allow_repository_default=allow_repository_default,
            )
        )

    return dedupe_runs(resolved_runs)


def resolve_runs_from_refs(
    refs: list[InferredRepositoryRef],
    latest_runs: list[Any],
) -> list[Any]:
    """프론트가 넘긴 답변 기준 ref를 현재 SQL run 객체로 되돌린다."""

    runs: list[Any] = []
    for ref in refs:
        if ref.run_id is not None:
            matched = next((run for run in latest_runs if run.id == ref.run_id), None)
            if matched is not None:
                runs.append(matched)
                continue

        matched = next(
            (
                run
                for run in latest_runs
                if run.repository_full_name == ref.repository_full_name
                and normalize_optional_text(run.branch) == normalize_optional_text(ref.branch)
                and (
                    not ref.commit_sha
                    or normalize_optional_text(run.commit_sha) == normalize_optional_text(ref.commit_sha)
                )
            ),
            None,
        )
        if matched is not None:
            runs.append(matched)
    return dedupe_runs(runs)


def resolve_runs_from_recent_list_ordinal(
    user_input: str,
    latest_runs: list[Any],
    messages: list[Any],
) -> list[Any]:
    """사용자가 숫자만 답하면 직전에 보여준 레포/브랜치 목록의 순번으로 해석한다."""

    match = BARE_ORDINAL_PATTERN.match(normalize_text(user_input))
    if not match:
        return []

    ordinal = int(match.group(1))
    for message in reversed(messages[:-1]):
        content = str(getattr(message, "content", ""))
        if "브랜치 목록입니다" in content:
            branch_runs = get_branch_runs_from_list_message(content, latest_runs)
            if 1 <= ordinal <= len(branch_runs):
                return [branch_runs[ordinal - 1]]
        if "레포지토리 목록입니다" in content:
            summaries = get_repository_summaries(latest_runs)
            if 1 <= ordinal <= len(summaries):
                return [summaries[ordinal - 1]["latest_run"]]
    return []


def resolve_single_repository_fallback(latest_runs: list[Any]) -> Any | None:
    """분석된 레포가 하나뿐이면 사용자가 이름을 생략해도 그 run을 기준으로 삼는다."""

    repository_names = {
        run.repository_full_name for run in latest_runs if run.repository_full_name
    }
    if len(repository_names) != 1:
        return None
    return latest_runs[0] if latest_runs else None


def build_next_basis_refs(
    current_refs: list[InferredRepositoryRef],
    target_runs: list[Any],
    mode: BasisMode,
) -> list[InferredRepositoryRef]:
    """사용자 요청 모드에 따라 다음 답변 기준 ref 목록을 만든다."""

    target_refs = [build_inferred_repository_ref(run) for run in target_runs]
    if mode == BASIS_MODE_CLEAR:
        return []
    if mode == BASIS_MODE_REPLACE:
        return target_refs
    if mode == BASIS_MODE_ADD:
        return dedupe_refs([*current_refs, *target_refs])
    if mode == BASIS_MODE_REMOVE:
        remove_keys = {repository_ref_key(ref) for ref in target_refs}
        return [
            ref
            for ref in current_refs
            if repository_ref_key(ref) not in remove_keys
        ]
    return target_refs


def build_repository_list_answer(latest_runs: list[Any]) -> str:
    """저장된 분석 run을 레포 단위 목록 답변으로 바꾼다."""

    summaries = get_repository_summaries(latest_runs)
    if not summaries:
        return "아직 분석된 레포지토리가 없습니다."

    lines = ["현재 분석된 레포지토리 목록입니다."]
    for index, summary in enumerate(summaries, start=1):
        latest = summary["latest_run"]
        lines.append(
            f"{index}. {summary['repository_full_name']} "
            f"- 브랜치 {summary['branch_count']}개, "
            f"마지막 분석 {format_indexed_at(latest)}"
        )
    return "\n".join(lines)


def build_branch_list_answer(
    user_input: str,
    latest_runs: list[Any],
    target_runs: list[Any],
    current_refs: list[InferredRepositoryRef],
    messages: list[Any] | None = None,
) -> str:
    """레포 이름을 기준으로 SQL에 저장된 브랜치 run 목록을 답변한다."""

    repository_names = find_repository_names_in_text(user_input, latest_runs)
    if not repository_names and target_runs:
        repository_names = [target_runs[0].repository_full_name]
    if not repository_names:
        repository_names = find_repository_names_by_branch_list_ordinal(
            user_input,
            latest_runs,
        )
    if not repository_names:
        repository_names = unique_repository_names_from_refs(current_refs)
    if not repository_names:
        repository_names = find_repository_names_by_ordinal(user_input, latest_runs)
    if not repository_names:
        repository_names = find_recent_repository_names(messages or [], latest_runs)

    if not repository_names:
        return (
            "어떤 레포지토리의 브랜치를 볼지 찾지 못했습니다. "
            "예: Jungle-303-04/warm-up 브랜치 목록처럼 물어봐 주세요."
        )

    lines: list[str] = []
    for repository_name in repository_names:
        branch_runs = [
            run for run in latest_runs if run.repository_full_name == repository_name
        ]
        if not branch_runs:
            lines.append(f"{repository_name}의 분석된 브랜치를 찾지 못했습니다.")
            continue

        lines.append(f"{repository_name}의 분석된 브랜치 목록입니다.")
        for index, run in enumerate(branch_runs, start=1):
            branch = run.branch or "기본 브랜치"
            lines.append(
                f"{index}. {branch} - 마지막 분석 {format_indexed_at(run)}, "
                f"코드 버전 {format_commit(run.commit_sha)}"
            )
    return "\n".join(lines)


def build_repository_target_search_answer(
    user_input: str,
    latest_runs: list[Any],
    target_runs: list[Any],
) -> str:
    """사용자가 말한 단어와 관련된 레포/브랜치 분석 run 명단을 답한다."""

    matched_runs = target_runs or find_runs_by_search_terms(user_input, latest_runs)
    if not matched_runs:
        return "조건에 맞는 분석 레포지토리나 브랜치를 찾지 못했습니다."

    lines = ["조건에 맞는 분석 대상입니다."]
    for index, run in enumerate(dedupe_runs(matched_runs), start=1):
        branch = run.branch or "기본 브랜치"
        lines.append(
            f"{index}. {run.repository_full_name} · {branch} "
            f"- 마지막 분석 {format_indexed_at(run)}, 코드 버전 {format_commit(run.commit_sha)}"
        )
    return "\n".join(lines)


def build_file_list_answer(
    user_input: str,
    target_runs: list[Any],
    file_snapshots_by_run: dict[int, list[Any]],
    skipped_files_by_run: dict[int, list[Any]],
    planned_focus: str | None = None,
) -> str:
    """확정된 run의 SQL 파일 스냅샷에서 파일/폴더 구조 질문에 답한다."""

    if not target_runs:
        return "어떤 레포지토리의 파일 구조를 볼지 찾지 못했습니다. 레포나 브랜치 기준을 먼저 정해 주세요."

    all_paths = [
        snapshot.path
        for snapshots in file_snapshots_by_run.values()
        for snapshot in snapshots
        if snapshot.path
    ]
    focus = detect_path_focus(user_input, all_paths, planned_focus=planned_focus)
    folder_only = is_folder_list_request(user_input)
    lines: list[str] = []
    for run in target_runs:
        snapshots = file_snapshots_by_run.get(run.id, [])
        skipped_files = skipped_files_by_run.get(run.id, [])
        paths = [snapshot.path for snapshot in snapshots if snapshot.path]
        if focus:
            paths = [path for path in paths if path_matches_focus(path, focus)]

        title = format_run_title(run)
        if focus:
            target_label = "폴더" if folder_only else "분석 파일"
            lines.append(f"{title}에서 '{focus}'와 관련된 {target_label}입니다.")
        elif folder_only:
            lines.append(f"{title}의 분석된 폴더 목록입니다.")
        else:
            lines.append(f"{title}의 분석된 파일 목록입니다.")

        result_paths = build_folder_paths(paths, focus) if folder_only else sorted(paths)
        if not result_paths:
            target_label = "폴더" if folder_only else "분석 파일"
            lines.append(f"- 조건에 맞는 {target_label}를 찾지 못했습니다.")
        else:
            for path in result_paths[:80]:
                lines.append(f"- {path}")
            if len(result_paths) > 80:
                lines.append(f"- ...외 {len(result_paths) - 80}개")

        if skipped_files and not focus:
            lines.append(f"- 참고: 미지원/제외 파일 {len(skipped_files)}개가 따로 기록되어 있습니다.")

    return "\n".join(lines)


def is_snapshot_comparison_question(user_input: str) -> bool:
    """두 개 이상의 선택 기준 사이의 코드 스냅샷 차이를 묻는 질문인지 본다."""

    text = normalize_text(user_input)
    return any(keyword in text for keyword in ("차이", "비교", "다른", "달라", "diff"))


def build_file_snapshot_comparison_answer(
    user_input: str,
    target_runs: list[Any],
    file_snapshots_by_run: dict[int, list[Any]],
) -> str:
    """SQL 파일 스냅샷 기준으로 추가, 삭제, 내용 변경 파일을 비교한다."""

    if len(target_runs) < 2:
        return "비교하려면 최소 두 개의 레포지토리/브랜치 기준이 필요합니다."

    lines = [
        "SQL 파일 스냅샷 기준 차이입니다.",
        "아직 코드 라인 diff가 아니라 파일 경로와 content_hash 기준의 MVP 비교입니다.",
    ]
    for item in build_snapshot_comparison_items(target_runs, file_snapshots_by_run):
        lines.append("")
        lines.append(f"기준 A: {format_run_title(item.base_run)}")
        lines.append(f"기준 B: {format_run_title(item.compare_run)}")
        lines.append(f"- B에만 있는 파일: {len(item.added_paths)}개")
        lines.append(f"- A에만 있는 파일: {len(item.removed_paths)}개")
        lines.append(f"- 경로는 같지만 내용 hash가 다른 파일: {len(item.changed_paths)}개")

        append_functional_difference_summary(
            lines=lines,
            user_input=user_input,
            base_run=item.base_run,
            compare_run=item.compare_run,
            added_paths=item.added_paths,
            removed_paths=item.removed_paths,
            changed_paths=item.changed_paths,
        )
        append_limited_paths(lines, "B에만 있음", item.added_paths)
        append_limited_paths(lines, "A에만 있음", item.removed_paths)
        append_limited_paths(lines, "내용 변경", item.changed_paths)

    return "\n".join(lines)


def build_snapshot_comparison_items(
    target_runs: list[Any],
    file_snapshots_by_run: dict[int, list[Any]],
) -> list[SnapshotComparisonItem]:
    """첫 번째 run을 기준으로 나머지 run과 파일 추가, 삭제, 변경을 계산한다."""

    if len(target_runs) < 2:
        return []

    base_run = target_runs[0]
    base_files = build_snapshot_map(file_snapshots_by_run.get(base_run.id, []))
    base_paths = set(base_files)
    items: list[SnapshotComparisonItem] = []

    for compare_run in target_runs[1:]:
        compare_files = build_snapshot_map(file_snapshots_by_run.get(compare_run.id, []))
        compare_paths = set(compare_files)
        changed_paths = sorted(
            path
            for path in base_paths & compare_paths
            if getattr(base_files[path], "content_hash", None)
            != getattr(compare_files[path], "content_hash", None)
        )
        items.append(
            SnapshotComparisonItem(
                base_run=base_run,
                compare_run=compare_run,
                added_paths=sorted(compare_paths - base_paths),
                removed_paths=sorted(base_paths - compare_paths),
                changed_paths=changed_paths,
            )
        )
    return items


def build_comparison_evidence_paths_by_run(
    user_input: str,
    comparison_items: list[SnapshotComparisonItem],
) -> dict[int, list[str]]:
    """스냅샷 차이 중 LLM에게 넘길 대표 파일 경로를 run별로 고른다."""

    exclude_frontend = asks_to_exclude_frontend(user_input)
    paths_by_run: dict[int, list[str]] = {}

    for item in comparison_items:
        for path in prioritize_comparison_paths(item.changed_paths):
            add_evidence_path(paths_by_run, item.base_run.id, path, exclude_frontend)
            add_evidence_path(paths_by_run, item.compare_run.id, path, exclude_frontend)
        for path in prioritize_comparison_paths(item.added_paths):
            add_evidence_path(paths_by_run, item.compare_run.id, path, exclude_frontend)
        for path in prioritize_comparison_paths(item.removed_paths):
            add_evidence_path(paths_by_run, item.base_run.id, path, exclude_frontend)

    return paths_by_run


def prioritize_comparison_paths(paths: list[str]) -> list[str]:
    """기능 차이 설명에 쓸 경로는 backend/app 쪽을 먼저 보게 한다."""

    return sorted(paths, key=build_comparison_path_priority)


def build_comparison_path_priority(path: str) -> tuple[int, str]:
    """백엔드 기능 코드, 문서, 프론트 순서로 대표 근거 경로를 정렬한다."""

    normalized = normalize_path(path)
    if normalized.startswith("backend/app/"):
        return (0, normalized)
    if normalized.startswith("backend/"):
        return (1, normalized)
    if normalized.startswith("docs/"):
        return (2, normalized)
    if normalized.startswith("frontend/"):
        return (4, normalized)
    return (3, normalized)


def add_evidence_path(
    paths_by_run: dict[int, list[str]],
    run_id: int,
    path: str,
    exclude_frontend: bool,
) -> None:
    """중복 없이 run별 대표 근거 경로 목록에 path를 추가한다."""

    normalized = normalize_path(path)
    if exclude_frontend and normalized.startswith("frontend/"):
        return

    paths = paths_by_run.setdefault(run_id, [])
    if len(paths) >= MAX_COMPARISON_EVIDENCE_PATHS_PER_RUN or path in paths:
        return
    paths.append(path)


def append_functional_difference_summary(
    lines: list[str],
    user_input: str,
    base_run: Any,
    compare_run: Any,
    added_paths: list[str],
    removed_paths: list[str],
    changed_paths: list[str],
) -> None:
    """파일 경로 diff를 기능 모듈 단위로 압축해 브랜치 간 차이를 읽기 쉽게 만든다."""

    exclude_frontend = asks_to_exclude_frontend(user_input)
    compare_only = summarize_functional_path_groups(added_paths, exclude_frontend)
    base_only = summarize_functional_path_groups(removed_paths, exclude_frontend)
    changed = summarize_functional_path_groups(changed_paths, exclude_frontend)

    if not compare_only and not base_only and not changed:
        return

    lines.append("")
    lines.append("기능 관점 요약:")
    if exclude_frontend:
        lines.append("- 사용자가 프론트 차이를 제외해 달라고 했으므로 frontend 경로는 요약에서 제외했습니다.")
    if compare_only:
        lines.append(
            f"- {format_run_title(compare_run)}에만 보이는 기능 영역: "
            f"{format_functional_group_summary(compare_only)}"
        )
    if base_only:
        lines.append(
            f"- {format_run_title(base_run)}에만 보이는 기능 영역: "
            f"{format_functional_group_summary(base_only)}"
        )
    if changed:
        lines.append(
            f"- 양쪽에 있지만 내용이 달라진 기능 영역: "
            f"{format_functional_group_summary(changed)}"
        )


def asks_to_exclude_frontend(user_input: str) -> bool:
    """사용자가 프론트/UI 차이가 아니라 기능 차이를 원한다고 말했는지 본다."""

    text = normalize_text(user_input)
    return any(keyword in text for keyword in ("프론트 말고", "프론트적인 차이 말고", "ui 말고"))


def summarize_functional_path_groups(
    paths: list[str],
    exclude_frontend: bool,
) -> dict[str, int]:
    """파일 path 목록을 backend/app 기능 폴더 중심의 count summary로 줄인다."""

    summary: dict[str, int] = {}
    for path in paths:
        group = detect_functional_path_group(path, exclude_frontend)
        if group is None:
            continue
        summary[group] = summary.get(group, 0) + 1
    return dict(sorted(summary.items(), key=lambda item: (-item[1], item[0])))


def detect_functional_path_group(path: str, exclude_frontend: bool) -> str | None:
    """경로를 기능 차이를 설명하기 좋은 단위로 접는다."""

    normalized = normalize_path(path)
    if exclude_frontend and normalized.startswith("frontend/"):
        return None

    parts = normalized.split("/")
    if len(parts) >= 3 and parts[0] == "backend" and parts[1] == "app":
        return "/".join(parts[:3])
    if len(parts) >= 2 and parts[0] == "backend":
        return "/".join(parts[:2])
    if parts[0] in {"docs", "frontend"}:
        return parts[0]
    return parts[0] if parts else None


def format_functional_group_summary(summary: dict[str, int], limit: int = 8) -> str:
    """기능 그룹 count를 한 줄 요약으로 만든다."""

    items = list(summary.items())
    labels = [f"{name}({count}개)" for name, count in items[:limit]]
    if len(items) > limit:
        labels.append(f"외 {len(items) - limit}개 영역")
    return ", ".join(labels)


def build_snapshot_map(snapshots: list[Any]) -> dict[str, Any]:
    """파일 path를 key로 삼아 같은 경로의 snapshot을 빠르게 비교하게 한다."""

    return {
        snapshot.path: snapshot
        for snapshot in snapshots
        if getattr(snapshot, "path", None)
    }


def append_limited_paths(
    lines: list[str],
    title: str,
    paths: list[str],
    limit: int = 12,
) -> None:
    """비교 결과가 너무 길어지지 않도록 대표 경로만 답변에 붙인다."""

    if not paths:
        return

    lines.append(f"{title}:")
    for path in paths[:limit]:
        lines.append(f"- {path}")
    if len(paths) > limit:
        lines.append(f"- ...외 {len(paths) - limit}개")


def build_current_basis_answer(current_refs: list[InferredRepositoryRef]) -> str:
    """현재 대화 turn이 들고 있는 답변 기준 ref를 사용자에게 보여준다."""

    if not current_refs:
        return "현재 고정된 답변 기준은 없습니다. 질문에 레포지토리 이름을 포함하면 해당 분석 결과를 찾아 답변합니다."

    lines = ["현재 답변 기준입니다."]
    for index, ref in enumerate(current_refs, start=1):
        lines.append(f"{index}. {format_response_ref(ref)}")
    return "\n".join(lines)


def build_basis_changed_answer(
    final_refs: list[InferredRepositoryRef],
    mode: BasisMode,
) -> str:
    """변경된 답변 기준을 사용자가 확인할 수 있는 문장으로 만든다."""

    if not final_refs:
        return "답변 기준을 비웠습니다. 다음 질문부터는 질문 내용에서 레포지토리를 찾아 답변합니다."

    action = {
        BASIS_MODE_ADD: "추가했습니다",
        BASIS_MODE_REMOVE: "변경했습니다",
        BASIS_MODE_REPLACE: "설정했습니다",
        BASIS_MODE_CLEAR: "비웠습니다",
    }.get(mode, "설정했습니다")
    lines = [f"앞으로 사용할 답변 기준을 {action}."]
    for index, ref in enumerate(final_refs, start=1):
        lines.append(f"{index}. {format_response_ref(ref)}")
    return "\n".join(lines)


def build_clarification_answer(latest_runs: list[Any]) -> str:
    """검색 기준을 확정하지 못했을 때 선택 가능한 레포 예시를 보여준다."""

    examples = ", ".join(
        summary["repository_full_name"]
        for summary in get_repository_summaries(latest_runs)[:3]
    )
    if examples:
        return f"어떤 레포지토리 기준으로 답할지 정하지 못했습니다. 예: {examples} 중 하나를 질문에 포함해 주세요."
    return "아직 분석된 레포지토리가 없습니다. 먼저 레포지토리를 등록하고 분석해 주세요."


def get_latest_unique_runs_by_repository_branch(runs: list[Any]) -> list[Any]:
    """같은 레포/브랜치가 여러 번 분석됐으면 가장 최근 run만 남긴다."""

    latest_runs = []
    seen_keys = set()
    for run in runs:
        if not run.repository_full_name:
            continue
        key = (run.repository_full_name, run.branch)
        if key in seen_keys:
            continue
        latest_runs.append(run)
        seen_keys.add(key)
    return latest_runs


def build_inferred_repository_ref(run: Any) -> InferredRepositoryRef:
    return InferredRepositoryRef(
        run_id=run.id,
        repository_full_name=run.repository_full_name,
        branch=run.branch,
        commit_sha=run.commit_sha,
    )


def format_response_ref(ref: InferredRepositoryRef) -> str:
    branch = ref.branch or "기본 브랜치"
    version = f" · 코드 버전 {format_commit(ref.commit_sha)}" if ref.commit_sha else ""
    return f"{ref.repository_full_name} · {branch}{version}"


def format_run_title(run: Any) -> str:
    branch = run.branch or "기본 브랜치"
    return f"{run.repository_full_name} · {branch} · 코드 버전 {format_commit(run.commit_sha)}"


def detect_path_focus(
    user_input: str,
    available_paths: list[str],
    planned_focus: str | None = None,
) -> str | None:
    """사용자가 특정 폴더를 말했으면 path 필터 키워드로 바꾼다."""

    if planned_focus and path_focus_exists(planned_focus, available_paths):
        return normalize_path(planned_focus)

    explicit_path = detect_explicit_path_focus(user_input, available_paths)
    if explicit_path:
        return explicit_path

    text = normalize_text(user_input)
    if "도메인" in text:
        return "domain"
    if "서비스" in text:
        return "service"
    if "라우터" in text:
        return "router"
    if "스키마" in text:
        return "schema"
    return None


def is_folder_list_request(user_input: str) -> bool:
    """사용자가 파일이 아니라 폴더/디렉토리 목록을 원한다고 말했는지 본다."""

    text = normalize_text(user_input)
    return any(keyword in text for keyword in ("폴더", "디렉토리", "directory"))


def build_folder_paths(paths: list[str], focus: str | None = None) -> list[str]:
    """저장된 파일 path 목록에서 실제 폴더 prefix만 추출한다."""

    folders = set()
    normalized_focus = normalize_path(focus) if focus else None
    for path in paths:
        segments = normalize_path(path).split("/")
        for index in range(1, len(segments)):
            folder = "/".join(segments[:index])
            if normalized_focus and not path_matches_focus(folder, normalized_focus):
                continue
            folders.add(folder)
    return sorted(folders)


def path_matches_focus(path: str, focus: str) -> bool:
    """폴더명과 파일명 모두에서 focus 단어가 포함되는지 확인한다."""

    normalized_path = normalize_path(path)
    normalized_focus = normalize_path(focus)
    if "/" in normalized_focus:
        return normalized_path == normalized_focus or normalized_path.startswith(
            f"{normalized_focus}/"
        )
    return normalized_focus in normalized_path


def detect_explicit_path_focus(
    user_input: str,
    available_paths: list[str],
) -> str | None:
    """사용자 입력에서 실제 저장된 path prefix와 가장 가까운 경로 표현을 찾는다."""

    path_candidates = build_user_path_candidates(user_input, available_paths)
    if not path_candidates:
        return None

    available_prefixes = build_available_path_prefixes(available_paths)
    for candidate in path_candidates:
        matched_prefix = find_best_path_prefix(candidate, available_prefixes)
        if matched_prefix:
            return matched_prefix
    return None


def build_user_path_candidates(
    user_input: str,
    available_paths: list[str],
) -> list[str]:
    """'백엔드/앱/어스', '백엔드에 앱에 어스' 같은 경로 후보를 normalize한다."""

    raw_candidates = PATH_TOKEN_PATTERN.findall(user_input)
    slash_candidate = build_korean_slash_path_candidate(user_input)
    if slash_candidate:
        raw_candidates.insert(0, slash_candidate)
    raw_candidates.extend(
        build_natural_language_path_candidates(user_input, available_paths)
    )

    candidates = []
    for candidate in raw_candidates:
        normalized = normalize_path(candidate)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def build_korean_slash_path_candidate(user_input: str) -> str | None:
    """한글 segment가 섞인 slash path를 실제 path segment 후보로 바꾼다."""

    if "/" not in user_input and "\\" not in user_input:
        return None

    raw_segments = [
        segment.strip()
        for segment in PATH_SEPARATOR_PATTERN.split(user_input)
        if segment.strip()
    ]
    if len(raw_segments) < 2:
        return None

    normalized_segments = []
    for segment in raw_segments:
        token = normalize_path_segment(segment)
        if token:
            normalized_segments.append(token)

    if len(normalized_segments) < 2:
        return None
    return "/".join(normalized_segments)


def build_natural_language_path_candidates(
    user_input: str,
    available_paths: list[str],
) -> list[str]:
    """쉼표, 조사, 공백으로 이어 말한 폴더 나열을 path 후보로 복원한다."""

    matched_segments = find_ordered_path_segments(
        user_input,
        build_available_path_segments(available_paths),
    )
    if len(matched_segments) < 2:
        return []

    candidates = ["/".join(matched_segments)]
    for start_index in range(1, len(matched_segments) - 1):
        candidates.append("/".join(matched_segments[start_index:]))
    return candidates


def find_ordered_path_segments(
    user_input: str,
    available_segments: set[str],
) -> list[str]:
    """사용자 문장에 등장한 실제/별칭 path segment를 등장 순서대로 수집한다."""

    text = normalize_text(user_input)
    ordered_segments: list[tuple[int, str]] = []

    for korean, english in KOREAN_PATH_SEGMENTS.items():
        start = text.find(korean)
        if start != -1:
            ordered_segments.append((start, english))

    for match in re.finditer(r"[a-zA-Z0-9_.-]+", text):
        token = match.group(0).lower()
        if token in available_segments:
            ordered_segments.append((match.start(), token))

    return dedupe_ordered_segments(ordered_segments)


def dedupe_ordered_segments(ordered_segments: list[tuple[int, str]]) -> list[str]:
    """같은 segment가 반복 매칭되어도 처음 나온 순서만 유지한다."""

    segments: list[str] = []
    seen = set()
    for _, segment in sorted(ordered_segments, key=lambda item: item[0]):
        if segment in seen:
            continue
        segments.append(segment)
        seen.add(segment)
    return segments


def build_available_path_segments(paths: list[str]) -> set[str]:
    """저장된 path에 실제로 존재하는 폴더/파일 segment 후보를 만든다."""

    segments = set()
    for path in paths:
        segments.update(segment for segment in normalize_path(path).split("/") if segment)
    return segments


def normalize_path_segment(segment: str) -> str | None:
    """문장 일부에서 path segment로 쓸 수 있는 마지막 단어를 꺼낸다."""

    text = normalize_text(segment)
    for korean, english in KOREAN_PATH_SEGMENTS.items():
        if korean in text:
            return english

    matches = re.findall(r"[a-zA-Z0-9_.-]+", text)
    if matches:
        return matches[-1].lower()
    return None


def build_available_path_prefixes(paths: list[str]) -> list[str]:
    """저장된 파일 path에서 실제 존재하는 폴더 prefix 후보를 만든다."""

    prefixes = set()
    for path in paths:
        segments = normalize_path(path).split("/")
        for index in range(1, len(segments)):
            prefixes.add("/".join(segments[:index]))
    return sorted(prefixes, key=lambda value: (-len(value), value))


def find_best_path_prefix(candidate: str, available_prefixes: list[str]) -> str | None:
    """사용자가 말한 경로와 실제 prefix를 앞에서부터 맞춘다."""

    for prefix in available_prefixes:
        if prefix == candidate or prefix.startswith(f"{candidate}/"):
            return candidate

    candidate_tail = candidate.split("/")[-1]
    for prefix in available_prefixes:
        if prefix.endswith(f"/{candidate_tail}") or prefix == candidate_tail:
            return prefix
    return None


def normalize_path(path: str) -> str:
    return PATH_SEPARATOR_PATTERN.sub("/", path.strip().lower()).strip("/")


def path_focus_exists(focus: str, available_paths: list[str]) -> bool:
    normalized_focus = normalize_path(focus)
    return any(path_matches_focus(path, normalized_focus) for path in available_paths)


def find_repository_names_in_text(user_input: str, latest_runs: list[Any]) -> list[str]:
    text = normalize_text(user_input)
    repository_names: list[str] = []
    seen_names = set()
    for run in latest_runs:
        repository_name = run.repository_full_name
        if not repository_name or repository_name in seen_names:
            continue
        if normalize_text(repository_name) in text:
            repository_names.append(repository_name)
            seen_names.add(repository_name)
    return repository_names


def find_repository_names_by_ordinal(user_input: str, latest_runs: list[Any]) -> list[str]:
    """사용자가 말한 '1번 레포'를 직전 레포 목록과 같은 정렬의 레포 이름으로 바꾼다."""

    repository_names: list[str] = []
    summaries = get_repository_summaries(latest_runs)
    for match in REPOSITORY_ORDINAL_PATTERN.finditer(normalize_text(user_input)):
        ordinal = int(match.group(1))
        if ordinal < 1 or ordinal > len(summaries):
            continue
        repository_name = summaries[ordinal - 1]["repository_full_name"]
        if repository_name not in repository_names:
            repository_names.append(repository_name)
    return repository_names


def find_repository_names_by_branch_list_ordinal(
    user_input: str,
    latest_runs: list[Any],
) -> list[str]:
    """'1 브랜치'처럼 레포 목록의 순번으로 브랜치 목록을 요청한 경우를 해석한다."""

    match = BRANCH_LIST_REPOSITORY_ORDINAL_PATTERN.match(normalize_text(user_input))
    if not match:
        return []

    ordinal = int(match.group(1))
    summaries = get_repository_summaries(latest_runs)
    if ordinal < 1 or ordinal > len(summaries):
        return []
    return [summaries[ordinal - 1]["repository_full_name"]]


def find_recent_repository_names(messages: list[Any], latest_runs: list[Any]) -> list[str]:
    """이전 대화에서 마지막으로 언급된 레포를 현재 질문의 생략된 기준으로 사용한다."""

    for message in reversed(messages[:-1]):
        repository_names = find_repository_names_in_text(
            str(getattr(message, "content", "")),
            latest_runs,
        )
        if repository_names:
            return repository_names[:1]
    return []


def get_branch_runs_from_list_message(content: str, latest_runs: list[Any]) -> list[Any]:
    """브랜치 목록 답변에 들어 있던 레포 이름으로 해당 레포의 최신 브랜치 run을 찾는다."""

    repository_names = find_repository_names_in_text(content, latest_runs)
    if not repository_names:
        return []
    return [
        run
        for run in latest_runs
        if run.repository_full_name == repository_names[0]
    ]


def resolve_runs_for_repository(
    user_input: str,
    latest_runs: list[Any],
    repository_name: str,
    allow_repository_default: bool = True,
) -> list[Any]:
    repository_runs = [
        run for run in latest_runs if run.repository_full_name == repository_name
    ]
    mentioned_branches = find_branch_names_in_text(user_input, repository_runs)
    if mentioned_branches:
        return [
            run
            for run in repository_runs
            if normalize_optional_text(run.branch) in mentioned_branches
        ]

    if not allow_repository_default:
        return []

    return repository_runs[:1]


def find_runs_by_search_terms(user_input: str, latest_runs: list[Any]) -> list[Any]:
    """문장에 남은 검색어가 레포명이나 브랜치명에 포함되는 run을 찾는다."""

    terms = extract_repository_target_search_terms(user_input)
    if not terms:
        return []

    matched_runs = []
    for run in latest_runs:
        searchable_text = normalize_text(
            f"{run.repository_full_name} {run.branch or ''}"
        )
        if any(term in searchable_text for term in terms):
            matched_runs.append(run)
    return dedupe_runs(matched_runs)


def extract_repository_target_search_terms(user_input: str) -> list[str]:
    """레포/브랜치 명단 요청 문장에서 실제 검색어처럼 보이는 단어만 남긴다."""

    text = normalize_text(user_input)
    for keyword in (
        "레포지토리",
        "레포",
        "저장소",
        "브랜치",
        "명단",
        "목록",
        "전부",
        "전체",
        "가져와",
        "가져",
        "보여줘",
        "보여",
        "알려줘",
        "알려",
        "들어간",
        "포함된",
        "포함",
        "찾아줘",
        "찾아",
        "검색",
        "이나",
        "나",
        "이",
        "가",
    ):
        text = text.replace(keyword, " ")

    terms = []
    for token in text.split():
        term = token.strip()
        if len(term) < 2:
            continue
        if term not in terms:
            terms.append(term)
    return terms


def find_branch_names_in_text(user_input: str, runs: list[Any]) -> set[str]:
    text = normalize_text(user_input)
    branches = set()
    branches.update(find_branch_names_by_ordinal(text, runs))
    for run in runs:
        branch = normalize_optional_text(run.branch)
        if branch and branch_matches_text(branch, text):
            branches.add(branch)
    return branches


def find_branch_names_by_ordinal(text: str, runs: list[Any]) -> set[str]:
    """사용자가 '1번 브랜치'처럼 말하면 현재 레포의 브랜치 목록 순번으로 해석한다."""

    if "브랜치" not in text:
        return set()

    branches = set()
    for match in BRANCH_ORDINAL_PATTERN.finditer(text):
        next_text = text[match.end() : match.end() + 8].lstrip()
        if next_text.startswith(("레포", "레포지토리", "저장소")):
            continue
        ordinal = int(match.group(1))
        if ordinal < 1 or ordinal > len(runs):
            continue
        branch = normalize_optional_text(runs[ordinal - 1].branch)
        if branch:
            branches.add(branch)
    return branches


def branch_matches_text(branch: str, text: str) -> bool:
    """브랜치 원문이나 구분자를 제거한 형태가 질문에 그대로 있는지 확인한다."""

    return any(key in text for key in build_branch_text_keys(branch))


def build_branch_text_keys(branch: str) -> set[str]:
    """하드코딩 별칭 없이 브랜치 원문 기반 후보만 만든다."""

    normalized_branch = normalize_optional_text(branch)
    keys = {normalized_branch}

    compact_branch = normalized_branch.replace("-", "").replace("_", "")
    keys.add(compact_branch)

    return {key for key in keys if key}


def get_repository_summaries(latest_runs: list[Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    seen = set()
    for run in latest_runs:
        repository_name = run.repository_full_name
        if not repository_name or repository_name in seen:
            continue
        repository_runs = [
            candidate
            for candidate in latest_runs
            if candidate.repository_full_name == repository_name
        ]
        summaries.append(
            {
                "repository_full_name": repository_name,
                "branch_count": len(repository_runs),
                "latest_run": repository_runs[0],
            }
        )
        seen.add(repository_name)
    return summaries


def dedupe_runs(runs: list[Any]) -> list[Any]:
    deduped_runs = []
    seen_ids = set()
    for run in runs:
        if run.id in seen_ids:
            continue
        deduped_runs.append(run)
        seen_ids.add(run.id)
    return deduped_runs


def dedupe_refs(refs: list[InferredRepositoryRef]) -> list[InferredRepositoryRef]:
    deduped_refs = []
    seen_keys = set()
    for ref in refs:
        key = repository_ref_key(ref)
        if key in seen_keys:
            continue
        deduped_refs.append(ref)
        seen_keys.add(key)
    return deduped_refs


def repository_ref_key(ref: InferredRepositoryRef) -> tuple[str, str, str]:
    return (
        ref.repository_full_name,
        normalize_optional_text(ref.branch),
        normalize_optional_text(ref.commit_sha),
    )


def unique_repository_names_from_refs(refs: list[InferredRepositoryRef]) -> list[str]:
    names = []
    seen = set()
    for ref in refs:
        if ref.repository_full_name in seen:
            continue
        names.append(ref.repository_full_name)
        seen.add(ref.repository_full_name)
    return names


def format_indexed_at(run: Any) -> str:
    value = getattr(run, "indexed_at", None)
    if value is None:
        return "분석 시각 없음"
    return value.strftime("%Y-%m-%d %H:%M")


def format_commit(commit_sha: str | None) -> str:
    if not commit_sha:
        return "확인 안 됨"
    return commit_sha[:7]


def normalize_optional_text(value: str | None) -> str:
    return str(value or "").strip().lower()
