import json
from dataclasses import dataclass

from app.agent.domain.chat import ChatMessage
from app.agent.service.repository_context import normalize_path
from app.rag.service.ports import TextGenerator


PATH_TARGET_SYSTEM_PROMPT = (
    "You resolve a user's folder/path request for a Korean coding assistant.\n"
    "The user may write typos, mixed Korean and English, missing separators, "
    "or rough pronunciation of folder names.\n\n"
    "Rules:\n"
    "- Choose ONLY one exact path from the provided path_candidates list.\n"
    "- Do not invent a path, repository, branch, or file name.\n"
    "- Use recent conversation only as context for what the user is referring to.\n"
    "- If the user is asking for all files and no specific path is clear, return null.\n"
    "- If several candidates are possible, choose the most specific clear candidate.\n\n"
    "Return JSON only in this exact shape:\n"
    '{"selected_path":"backend/app/auth","reason":"short reason"}\n'
    'If unclear, return: {"selected_path":null,"reason":"short reason"}'
)
MAX_PATH_CANDIDATES = 220
MAX_RECENT_MESSAGES = 6
MAX_MESSAGE_CHARS = 300


@dataclass(frozen=True)
class PathTargetPlan:
    """LLM이 고른 실제 SQL path prefix 하나."""

    selected_path: str | None
    reason: str | None = None


class AgentPathTargetResolver:
    """사용자의 흐릿한 폴더 표현을 실제 저장된 path prefix 후보 중 하나로 제한한다."""

    def __init__(self, text_generator: TextGenerator) -> None:
        self.text_generator = text_generator

    def resolve_path_target(
        self,
        user_input: str,
        path_candidates: list[str],
        messages: list[ChatMessage],
    ) -> PathTargetPlan:
        """LLM 결과를 후보 목록으로 다시 검증해 잘못 만든 path를 버린다."""

        normalized_candidates = normalize_candidates(path_candidates)
        if not normalized_candidates:
            return PathTargetPlan(selected_path=None, reason="no path candidates")

        try:
            response = self.text_generator.generate(
                [
                    {"role": "system", "content": PATH_TARGET_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_path_target_prompt(
                            user_input=user_input,
                            path_candidates=normalized_candidates,
                            messages=messages,
                        ),
                    },
                ]
            )
        except Exception as exc:
            return PathTargetPlan(
                selected_path=None,
                reason=f"path target resolver failed: {exc}",
            )

        return parse_path_target_response(response, normalized_candidates)


def build_path_target_prompt(
    user_input: str,
    path_candidates: list[str],
    messages: list[ChatMessage],
) -> str:
    """LLM이 후보 밖 path를 만들지 않도록 실제 prefix 목록을 JSON으로 제공한다."""

    return (
        "Recent conversation:\n"
        f"{format_recent_messages(messages)}\n\n"
        "User message:\n"
        f"{user_input.strip()}\n\n"
        "path_candidates:\n"
        f"{json.dumps(path_candidates[:MAX_PATH_CANDIDATES], ensure_ascii=False)}\n\n"
        "Select one path from path_candidates, or null."
    )


def parse_path_target_response(
    response: str,
    path_candidates: list[str],
) -> PathTargetPlan:
    """LLM JSON에서 selected_path를 꺼내되 실제 후보에 있는 값만 인정한다."""

    try:
        payload = json.loads(extract_json_object(response))
    except (json.JSONDecodeError, TypeError):
        return PathTargetPlan(selected_path=None, reason="invalid json")

    selected_path = payload.get("selected_path")
    reason = payload.get("reason") if isinstance(payload.get("reason"), str) else None
    if selected_path is None:
        return PathTargetPlan(selected_path=None, reason=reason)
    if not isinstance(selected_path, str):
        return PathTargetPlan(selected_path=None, reason="selected_path is not string")

    selected_path = normalize_path(selected_path)
    candidate_by_path = {normalize_path(candidate): candidate for candidate in path_candidates}
    if selected_path not in candidate_by_path:
        return PathTargetPlan(selected_path=None, reason="selected_path is not a candidate")

    return PathTargetPlan(selected_path=candidate_by_path[selected_path], reason=reason)


def normalize_candidates(path_candidates: list[str]) -> list[str]:
    """중복과 빈 값을 제거해 LLM에게 줄 후보 목록을 짧고 안정적으로 만든다."""

    normalized = []
    seen = set()
    for candidate in path_candidates:
        value = normalize_path(candidate)
        if not value or value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    return normalized


def format_recent_messages(messages: list[ChatMessage]) -> str:
    """짧은 후속 질문을 해석할 만큼의 최근 대화만 prompt에 넣는다."""

    if not messages:
        return "(none)"

    formatted_messages = []
    for message in messages[-MAX_RECENT_MESSAGES:]:
        content = message.content.strip().replace("\n", " ")
        if len(content) > MAX_MESSAGE_CHARS:
            content = f"{content[:MAX_MESSAGE_CHARS]}..."
        formatted_messages.append(f"{message.role}: {content}")
    return "\n".join(formatted_messages)


def extract_json_object(value: str) -> str:
    """모델이 설명을 붙여도 첫 JSON object만 파싱한다."""

    text = value.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]
