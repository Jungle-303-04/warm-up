import json
from dataclasses import dataclass

from app.agent.domain.chat import ChatMessage
from app.agent.service.agent_intent import (
    BASIS_MODE_ADD,
    BASIS_MODE_CLEAR,
    BASIS_MODE_REMOVE,
    BASIS_MODE_REPLACE,
    INTENT_CHANGE_BASIS,
    INTENT_GENERAL_CHAT,
    INTENT_LIST_BRANCHES,
    INTENT_LIST_FILES,
    INTENT_LIST_REPOSITORIES,
    INTENT_RAG_ANSWER,
    INTENT_SHOW_BASIS,
    AgentIntent,
    BasisMode,
    normalize_text,
)
from app.rag.service.ports import TextGenerator


VALID_INTENTS = {
    INTENT_LIST_REPOSITORIES,
    INTENT_LIST_BRANCHES,
    INTENT_LIST_FILES,
    INTENT_SHOW_BASIS,
    INTENT_CHANGE_BASIS,
    INTENT_RAG_ANSWER,
    INTENT_GENERAL_CHAT,
}
VALID_BASIS_MODES = {
    BASIS_MODE_REPLACE,
    BASIS_MODE_ADD,
    BASIS_MODE_REMOVE,
    BASIS_MODE_CLEAR,
}
DEFAULT_INTENT = INTENT_RAG_ANSWER
DEFAULT_BASIS_MODE = BASIS_MODE_REPLACE
FALLBACK_REASON_PREFIX = "intent resolver failed"

INTENT_RESOLVER_SYSTEM_PROMPT = (
    "You classify a Korean coding assistant chat message into one intent. "
    "Return JSON only. Do not answer the user.\n\n"
    "Intents:\n"
    "- list_repositories: user asks what repositories are registered/indexed/analyzed. "
    "Examples: '무슨 레포들이 있지?', '분석된 저장소 뭐 있어?', '레포 보여줘', 'ㄹㅍㅁㄹ', 'ㄿㅁㄹ'.\n"
    "- list_branches: user asks branch list for a repository. "
    "Examples: '1 ㅂㄹㅊ', '1번 레포 브랜치', 'Jungle-303-04/warm-up 브랜치 목록'.\n"
    "- list_files: user asks what files/folders/directories exist in the selected repository snapshot. "
    "Examples: '도메인 폴더가 뭐가 있지?', '우녕 브랜치의 모든 파일', '파일 구조 보여줘'.\n"
    "- show_basis: user asks current answer basis/context.\n"
    "- change_basis: user wants to set/add/remove/clear answer basis.\n"
    "  Bare numbers like '1' or '3번' after a repository/branch list usually mean change_basis. "
    "  But an ordinal followed by a branch word or branch shorthand means list_branches, not change_basis. "
    "Commands like '다시 빼', '그거 빼', '기준 빼' also mean change_basis with basis_mode remove.\n"
    "- general_chat: greeting or casual talk not asking repository/code facts.\n"
    "- rag_answer: code, plan, implementation, document, or repository content question.\n\n"
    "For change_basis, set basis_mode to replace/add/remove/clear. "
    "For other intents, basis_mode must be null.\n\n"
    "Output shape:\n"
    '{"intent":"list_repositories","basis_mode":null,"reason":"short reason"}'
)


@dataclass(frozen=True)
class AgentIntentPlan:
    """LLM이 고른 질문 의도와 기준 변경 모드."""

    intent: AgentIntent
    basis_mode: BasisMode | None = None
    reason: str | None = None


class AgentIntentResolver:
    """키워드 분기가 놓친 자연어 입력을 LLM으로 intent JSON에 매핑한다."""

    def __init__(self, text_generator: TextGenerator) -> None:
        self.text_generator = text_generator

    def resolve_intent(
        self,
        user_input: str,
        messages: list[ChatMessage],
    ) -> AgentIntentPlan:
        """사용자 입력과 짧은 대화 맥락을 보고 안전한 intent 값 하나를 고른다."""

        try:
            response = self.text_generator.generate(
                [
                    {"role": "system", "content": INTENT_RESOLVER_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_intent_prompt(user_input, messages),
                    },
                ]
            )
        except Exception as exc:
            return AgentIntentPlan(
                intent=DEFAULT_INTENT,
                basis_mode=None,
                reason=f"{FALLBACK_REASON_PREFIX}: {exc}",
            )

        return parse_intent_response(response)


def build_intent_prompt(user_input: str, messages: list[ChatMessage]) -> str:
    """최근 대화와 현재 입력을 LLM이 분류하기 쉬운 짧은 텍스트로 묶는다."""

    return (
        "Recent conversation:\n"
        f"{format_recent_messages(messages)}\n\n"
        "Current user message:\n"
        f"{user_input.strip()}\n\n"
        "Normalized current user message:\n"
        f"{normalize_text(user_input)}"
    )


def parse_intent_response(response: str) -> AgentIntentPlan:
    """LLM JSON에서 허용된 intent와 basis_mode만 안전하게 꺼낸다."""

    try:
        payload = json.loads(extract_json_object(response))
    except (json.JSONDecodeError, TypeError):
        return AgentIntentPlan(intent=DEFAULT_INTENT)

    intent = payload.get("intent")
    if intent not in VALID_INTENTS:
        intent = DEFAULT_INTENT

    basis_mode = payload.get("basis_mode")
    if intent != INTENT_CHANGE_BASIS:
        basis_mode = None
    elif basis_mode not in VALID_BASIS_MODES:
        basis_mode = DEFAULT_BASIS_MODE

    reason = payload.get("reason") if isinstance(payload.get("reason"), str) else None
    return AgentIntentPlan(
        intent=intent,
        basis_mode=basis_mode,
        reason=reason,
    )


def extract_json_object(value: str) -> str:
    """모델이 설명을 섞더라도 첫 JSON object만 파싱한다."""

    text = value.strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


def format_recent_messages(messages: list[ChatMessage]) -> str:
    """intent 판단에 필요한 최근 대화만 짧게 제공한다."""

    if not messages:
        return "(none)"

    formatted_messages = []
    for message in messages[-6:]:
        content = message.content.strip().replace("\n", " ")
        if len(content) > 300:
            content = f"{content[:300]}..."
        formatted_messages.append(f"{message.role}: {content}")
    return "\n".join(formatted_messages)
