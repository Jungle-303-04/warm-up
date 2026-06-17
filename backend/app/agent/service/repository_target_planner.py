import json
from dataclasses import dataclass
from typing import Any

from app.agent.domain.chat import ChatMessage, InferredRepositoryRef
from app.agent.service.agent_intent import is_bare_target_selection
from app.rag.service.ports import TextGenerator


TARGET_PLANNER_SYSTEM_PROMPT = (
    "You are a repository target planner for a coding assistant. Your task is to select the appropriate "
    "repository/branch targets based on the user's question.\n\n"
    "Rules:\n"
    "- The candidates are SQL metadata for already indexed repository runs. "
    "You must select only from these candidates.\n"
    "- Use the recent conversation to resolve short follow-up replies such as '3', '3번', "
    "'그거', or branch names mentioned after a branch list was shown.\n"
    "- A bare number from the user usually means the ordinal number in the latest visible list, "
    "not an internal database id.\n"
    "- If recent conversation makes the omitted repository or branch clear, use that context.\n"
    "- If the user writes a typo, Korean nickname, partial repository name, or partial branch name, "
    "infer the closest candidate only when the candidate is clear from the candidate list and conversation.\n"
    "- Branch names may be romanized Korean names. A Korean phonetic mention or typo can refer to "
    "a romanized branch candidate when it is clearly closer than the other branch candidates.\n"
    "- If the user message contains multiple target-like words, do not ignore the later words. "
    "When a later word plausibly points to a branch, choose that branch instead of defaulting to "
    "the newest run for the repository.\n"
    "- If the user names one repository and branch, choose the newest matching run for that branch.\n"
    "- If the user names one repository without any branch-like word, choose the newest run for that repository.\n"
    "- If selection_mode is single_best_target, return exactly one best repository_full_name/branch pair unless no candidate is clear. "
    "Do not return every branch of the repository in this mode.\n"
    "- If the user asks to remove/exclude answer basis, select the runs to remove, not the runs to keep. "
    "When removing a repository without a branch name, select all matching candidate runs for that repository.\n"
    "- If the user says 'A 빼고 B로/으로', 'A 말고 B', or equivalent, select only replacement target B. "
    "Do not select excluded target A.\n"
    "- If the user asks to compare or use multiple repositories or branches, choose all needed newest matching runs.\n"
    "- If neither the question nor recent conversation identifies a repository clearly and there is more than one repository, choose none.\n"
    "- If there is exactly one available repository and the question is about code, you may choose its newest run.\n"
    "- Do not invent repository names, branches, or commits. "
    "Use ONLY the repository_full_name and branch values provided in the candidates.\n\n"
    "Output Format:\n"
    "Answer with JSON only in this exact shape:\n"
    '{"selected_targets": [{"repository_full_name": "owner/repo", "branch": "main"}], "reason": "short reason"}\n'
    'If none can be selected, return: {"selected_targets": [], "reason": "short reason"}'
)
NO_SELECTION_REASON = "no matching repository target"


@dataclass(frozen=True)
class RepositoryTargetPlan:
    """LLM target planner가 고른 답변 기준 ref 목록."""

    inferred_repository_refs: list[InferredRepositoryRef] | None
    reason: str | None = None


class AgentRepositoryTargetPlanner:
    """사용자 질문과 분석 후보 목록을 보고 LLM으로 답변 기준을 고른다."""

    def __init__(self, text_generator: TextGenerator) -> None:
        self.text_generator = text_generator

    def infer_repository_refs(
        self,
        user_input: str,
        runs: list[Any],
        messages: list[ChatMessage],
    ) -> RepositoryTargetPlan:
        """질문에 필요한 레포/브랜치 기준을 분석 후보 중에서 선택한다."""

        if not runs:
            return RepositoryTargetPlan(
                inferred_repository_refs=None,
                reason="no indexed repository runs",
            )

        try:
            planner_response = self.text_generator.generate(
                [
                    {"role": "system", "content": TARGET_PLANNER_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_planner_prompt(
                            user_input,
                            runs,
                            messages,
                        ),
                    },
                ]
            )
        except Exception as exc:
            return RepositoryTargetPlan(
                inferred_repository_refs=None,
                reason=f"repository target planner failed: {exc}",
            )
        matched_runs = pick_runs_by_targets(
            runs,
            parse_selected_targets(planner_response),
        )
        if not matched_runs:
            return RepositoryTargetPlan(
                inferred_repository_refs=None,
                reason=NO_SELECTION_REASON,
            )

        return RepositoryTargetPlan(
            inferred_repository_refs=[
                build_inferred_repository_ref(run)
                for run in matched_runs
            ],
            reason=None,
        )


def build_planner_prompt(
    user_input: str,
    runs: list[Any],
    messages: list[ChatMessage],
) -> str:
    """LLM이 후보 밖 값을 만들지 않도록 분석 후보를 명확한 JSON 배열로 제공한다."""

    candidates = [
        {
            "repository_full_name": run.repository_full_name,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "indexed_at": run.indexed_at.isoformat() if run.indexed_at else None,
        }
        for run in runs
        if run.repository_full_name
    ]
    selection_mode = (
        "single_best_target"
        if is_bare_target_selection(user_input)
        else "question_or_multi_target"
    )

    return (
        "Recent conversation:\n"
        f"{format_recent_messages(messages)}\n\n"
        "User question:\n"
        f"{user_input.strip()}\n\n"
        "selection_mode:\n"
        f"{selection_mode}\n\n"
        "Available repository analysis candidates (sorted from newest to oldest):\n"
        f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "Based on the system rules, choose which repository_full_name and branch values should be used."
    )


def format_recent_messages(messages: list[ChatMessage]) -> str:
    """planner가 대화 맥락을 보되 prompt가 과하게 커지지 않도록 최근 메시지만 넣는다."""

    if not messages:
        return "(none)"

    formatted_messages = []
    for message in messages[-8:]:
        content = message.content.strip().replace("\n", " ")
        if len(content) > 500:
            content = f"{content[:500]}..."
        formatted_messages.append(f"{message.role}: {content}")
    return "\n".join(formatted_messages)


def parse_selected_targets(planner_response: str) -> list[dict[str, str | None]]:
    """LLM 응답에서 레포/브랜치 target만 꺼내 후보 매핑에 사용할 형태로 정리한다."""

    try:
        payload = json.loads(extract_json_object(planner_response))
    except (json.JSONDecodeError, TypeError):
        return []

    selected_targets = payload.get("selected_targets")
    if not isinstance(selected_targets, list):
        return []

    targets = []
    for target in selected_targets:
        if not isinstance(target, dict):
            continue
        repository_full_name = target.get("repository_full_name")
        branch = target.get("branch")
        if not isinstance(repository_full_name, str) or not repository_full_name.strip():
            continue
        if branch is not None and not isinstance(branch, str):
            continue
        targets.append(
            {
                "repository_full_name": repository_full_name.strip(),
                "branch": branch.strip() if isinstance(branch, str) else None,
            }
        )
    return targets


def extract_json_object(value: str) -> str:
    """모델이 실수로 짧은 설명을 붙여도 첫 JSON object만 파싱한다."""

    text = value.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


def pick_runs_by_targets(
    runs: list[Any],
    selected_targets: list[dict[str, str | None]],
) -> list[Any]:
    """LLM이 고른 레포/브랜치 이름을 실제 최신 SQL run 객체로 매핑한다."""

    picked_runs = []
    seen_matches = set()
    for target in selected_targets:
        run = find_run_by_target(runs, target)
        if run is None or run.id in seen_matches:
            continue
        picked_runs.append(run)
        seen_matches.add(run.id)
    return picked_runs


def find_run_by_target(
    runs: list[Any],
    target: dict[str, str | None],
) -> Any | None:
    """레포명과 브랜치명으로 실제 최신 SQL run 후보를 다시 찾는다."""

    repository_full_name = target["repository_full_name"]
    branch = target.get("branch")
    for run in runs:
        if run.repository_full_name != repository_full_name:
            continue
        if branch is None:
            return run
        if normalize_optional_text(run.branch) == normalize_optional_text(branch):
            return run
    return None


def build_inferred_repository_ref(run: Any) -> InferredRepositoryRef:
    """최신 run 선택 결과를 프론트에 돌려줄 추론 결과로 바꾼다."""

    return InferredRepositoryRef(
        run_id=run.id,
        repository_full_name=run.repository_full_name,
        branch=run.branch,
        commit_sha=run.commit_sha,
    )


def normalize_optional_text(value: str | None) -> str:
    return str(value or "").strip().lower()
