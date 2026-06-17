import re
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


def build_file_list_answer(
    user_input: str,
    target_runs: list[Any],
    file_snapshots_by_run: dict[int, list[Any]],
    skipped_files_by_run: dict[int, list[Any]],
) -> str:
    """확정된 run의 SQL 파일 스냅샷에서 파일/폴더 구조 질문에 답한다."""

    if not target_runs:
        return "어떤 레포지토리의 파일 구조를 볼지 찾지 못했습니다. 레포나 브랜치 기준을 먼저 정해 주세요."

    focus = detect_path_focus(user_input)
    lines: list[str] = []
    for run in target_runs:
        snapshots = file_snapshots_by_run.get(run.id, [])
        skipped_files = skipped_files_by_run.get(run.id, [])
        paths = [snapshot.path for snapshot in snapshots if snapshot.path]
        if focus:
            paths = [path for path in paths if path_matches_focus(path, focus)]

        title = format_run_title(run)
        if focus:
            lines.append(f"{title}에서 '{focus}'와 관련된 분석 파일입니다.")
        else:
            lines.append(f"{title}의 분석된 파일 목록입니다.")

        if not paths:
            lines.append("- 조건에 맞는 분석 파일을 찾지 못했습니다.")
        else:
            for path in sorted(paths)[:80]:
                lines.append(f"- {path}")
            if len(paths) > 80:
                lines.append(f"- ...외 {len(paths) - 80}개")

        if skipped_files and not focus:
            lines.append(f"- 참고: 미지원/제외 파일 {len(skipped_files)}개가 따로 기록되어 있습니다.")

    return "\n".join(lines)


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


def detect_path_focus(user_input: str) -> str | None:
    """사용자가 특정 폴더를 말했으면 path 필터 키워드로 바꾼다."""

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


def path_matches_focus(path: str, focus: str) -> bool:
    """폴더명과 파일명 모두에서 focus 단어가 포함되는지 확인한다."""

    return focus in normalize_text(path.replace("\\", "/"))


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
