import json
from dataclasses import dataclass
from typing import Any

from app.agent.domain.chat import ChatMessage, InferredRepositoryRef
from app.rag.service.ports import TextGenerator


TARGET_PLANNER_SYSTEM_PROMPT = (
    "You are a repository target planner for a coding assistant. Your task is to select the appropriate "
    "repository analysis runs based on the user's question.\n\n"
    "Rules:\n"
    "- The candidates are SQL metadata for already indexed repository runs. "
    "You must select only from these candidates.\n"
    "- Use the recent conversation to resolve short follow-up replies such as '3', '3번', "
    "'그거', or branch names mentioned after a branch list was shown.\n"
    "- A bare number from the user usually means the ordinal number in the latest visible list, "
    "not a database run_id, unless the user explicitly says run_id.\n"
    "- If recent conversation makes the omitted repository or branch clear, use that context.\n"
    "- If the user writes a typo, Korean nickname, partial repository name, or partial branch name, "
    "infer the closest candidate only when the candidate is clear from the candidate list and conversation.\n"
    "- If the user names one repository and branch, choose the newest matching run for that branch.\n"
    "- If the user names one repository without a branch, choose the newest run for that repository.\n"
    "- If the user asks to remove/exclude answer basis, select the runs to remove, not the runs to keep. "
    "When removing a repository without a branch name, select all matching candidate runs for that repository.\n"
    "- If the user asks to compare or use multiple repositories or branches, choose all needed newest matching runs.\n"
    "- If neither the question nor recent conversation identifies a repository clearly and there is more than one repository, choose none.\n"
    "- If there is exactly one available repository and the question is about code, you may choose its newest run.\n"
    "- Do not invent repository names, branches, commits, or run_ids. "
    "Use ONLY the run_id values provided in the candidates.\n\n"
    "Output Format:\n"
    "Answer with JSON only in this exact shape:\n"
    '{"selected_run_ids": [1, 2], "reason": "short reason"}\n'
    'If none can be selected, return: {"selected_run_ids": [], "reason": "short reason"}'
)
NO_SELECTION_REASON = "no matching repository analysis run"


@dataclass(frozen=True) # immutable
class RepositoryTargetPlan:
    """LLM target planner가 고른 답변 기준 run 목록."""

    inferred_repository_refs: list[InferredRepositoryRef] | None
    reason: str | None = None


class AgentRepositoryTargetPlanner:
    """사용자 질문과 SQL run 후보 목록을 보고 LLM으로 답변 기준을 고른다."""

    def __init__(self, text_generator: TextGenerator) -> None:
        self.text_generator = text_generator

    def infer_repository_refs(
        self,
        user_input: str,
        runs: list[Any],
        messages: list[ChatMessage],
    ) -> RepositoryTargetPlan:
        """질문에 필요한 레포/브랜치 기준을 후보 run 중에서 선택한다."""

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
        selected_run_ids = parse_selected_run_ids(planner_response)
        if not selected_run_ids:
            return RepositoryTargetPlan(
                inferred_repository_refs=None,
                reason=NO_SELECTION_REASON,
            )

        selected_runs = pick_runs_by_id(runs, selected_run_ids)
        if not selected_runs:
            return RepositoryTargetPlan(
                inferred_repository_refs=None,
                reason=NO_SELECTION_REASON,
            )

        return RepositoryTargetPlan(
            inferred_repository_refs=[
                build_inferred_repository_ref(run)
                for run in selected_runs
            ],
            reason=None,
        )


def build_planner_prompt(
    user_input: str,
    runs: list[Any],
    messages: list[ChatMessage],
) -> str:
    """LLM이 후보 밖 값을 만들지 않도록 run 후보를 명확한 JSON 배열로 제공한다."""

    candidates = [
        {
            "run_id": run.id,
            "repository_full_name": run.repository_full_name,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "indexed_at": run.indexed_at.isoformat() if run.indexed_at else None,
        }
        for run in runs
        if run.repository_full_name
    ]

    return (
        "Recent conversation:\n"
        f"{format_recent_messages(messages)}\n\n"
        "User question:\n"
        f"{user_input.strip()}\n\n"
        "Available repository analysis runs (sorted from newest to oldest):\n"
        f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "Based on the system rules, choose which run_id values should be used."
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


def parse_selected_run_ids(planner_response: str) -> list[int]:
    """LLM 응답에서 selected_run_ids만 안전하게 추출한다."""

    try:
        payload = json.loads(extract_json_object(planner_response))
    except (json.JSONDecodeError, TypeError):
        return []

    selected_run_ids = payload.get("selected_run_ids")
    if not isinstance(selected_run_ids, list):
        return []

    return [
        run_id
        for run_id in selected_run_ids
        if isinstance(run_id, int) and run_id > 0
    ]


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


def pick_runs_by_id(runs: list[Any], selected_run_ids: list[int]) -> list[Any]:
    """LLM이 선택한 run_id 순서를 유지하되 후보에 없는 값은 버린다."""

    run_by_id = {run.id: run for run in runs}
    picked_runs = []
    seen_run_ids = set()

    for run_id in selected_run_ids:
        run = run_by_id.get(run_id)
        if run is None or run_id in seen_run_ids:
            continue
        picked_runs.append(run)
        seen_run_ids.add(run_id)

    return picked_runs


def build_inferred_repository_ref(run: Any) -> InferredRepositoryRef:
    """최신 run 선택 결과를 프론트에 돌려줄 추론 결과로 바꾼다."""

    return InferredRepositoryRef(
        run_id=run.id,
        repository_full_name=run.repository_full_name,
        branch=run.branch,
        commit_sha=run.commit_sha,
    )
