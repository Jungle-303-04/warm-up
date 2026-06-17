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
    INTENT_SEARCH_REPOSITORY_TARGETS,
    INTENT_RAG_ANSWER,
    INTENT_SHOW_BASIS,
    AgentIntent,
    BasisMode,
    normalize_text,
)
from app.agent.service.agent_tool_registry import (
    TOOL_CHANGE_BASIS,
    TOOL_CLARIFY,
    TOOL_COMPARE_SNAPSHOTS,
    TOOL_GENERAL_CHAT,
    TOOL_LIST_BRANCHES,
    TOOL_LIST_FILES,
    TOOL_LIST_REPOSITORIES,
    TOOL_RETRIEVE_RAG,
    TOOL_SEARCH_REPOSITORY_TARGETS,
    TOOL_SHOW_BASIS,
)
from app.rag.service.ports import TextGenerator


VALID_INTENTS = {
    INTENT_LIST_REPOSITORIES,
    INTENT_LIST_BRANCHES,
    INTENT_SEARCH_REPOSITORY_TARGETS,
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
VALID_TOOL_NAMES = {
    TOOL_LIST_REPOSITORIES,
    TOOL_LIST_BRANCHES,
    TOOL_SEARCH_REPOSITORY_TARGETS,
    TOOL_LIST_FILES,
    TOOL_SHOW_BASIS,
    TOOL_CHANGE_BASIS,
    TOOL_RETRIEVE_RAG,
    TOOL_COMPARE_SNAPSHOTS,
    TOOL_GENERAL_CHAT,
    TOOL_CLARIFY,
}
DEFAULT_INTENT = INTENT_RAG_ANSWER
DEFAULT_BASIS_MODE = BASIS_MODE_REPLACE
FALLBACK_REASON_PREFIX = "intent resolver failed"

INTENT_RESOLVER_SYSTEM_PROMPT = (
    "You are the planner for a Korean code-analysis agent. "
    "Classify the user message and choose the next tool. "
    "Return JSON only. Do not answer the user.\n\n"
    "Intents:\n"
    "- list_repositories: user asks what repositories are registered/indexed/analyzed. "
    "Examples: '무슨 레포들이 있지?', '분석된 저장소 뭐 있어?', '레포 보여줘', "
    "'레포 이름', '레포명', 'ㄹㅍㅁㄹ', 'ㄿㅁㄹ'.\n"
    "- list_branches: user asks branch list for a repository. "
    "Examples: '1 ㅂㄹㅊ', '1번 레포 브랜치', 'Jungle-303-04/warm-up 브랜치 목록'.\n"
    "- search_repository_targets: user asks to find/list repositories or branches containing a word. "
    "Examples: '민정이 들어간 레포나 브랜치 명단 전부 가져와', 'minjeong 포함된 브랜치 찾아줘'.\n"
    "- list_files: user asks what files/folders/directories exist in the selected repository snapshot. "
    "Examples: '도메인 폴더가 뭐가 있지?', '우녕 브랜치의 모든 파일', '파일 구조 보여줘', "
    "'백엔드에 앱에 어스에 있는 거 전부 줘', '백엔드, 앱, 어스 안에꺼'. "
    "This also includes noisy folder/path requests with typos, mixed Korean-English, "
    "romanized folder names, missing separators, or shorthand.\n"
    "- show_basis: user asks current answer basis/context.\n"
    "- change_basis: user wants to set/add/remove/clear answer basis.\n"
    "  Bare numbers like '1' or '3번' after a repository/branch list usually mean change_basis. "
    "  But an ordinal followed by a branch word or branch shorthand means list_branches, not change_basis. "
    "  If the message mainly names or selects a repository/branch without asking a content question, "
    "classify it as change_basis with basis_mode replace. "
    "Commands like '다시 빼', '그거 빼', '기준 빼', '민정 브랜치 빼', '우녕 빼' "
    "also mean change_basis with basis_mode remove. "
    "Commands like '우녕 빼고 민정으로 하자' mean change_basis with basis_mode replace, "
    "selecting the replacement target only.\n"
    "- general_chat: greeting or casual talk not asking repository/code facts.\n"
    "- rag_answer: code, plan, implementation, document, or repository content question.\n\n"
    "Tool choices:\n"
    "- list_repositories: show analyzed repository list from SQL metadata.\n"
    "- list_branches: show analyzed branch list from SQL metadata.\n"
    "- search_repository_targets: search repository/branch names from SQL metadata.\n"
    "- list_files: show file/folder snapshot list from SQL metadata.\n"
    "- show_basis: show current answer basis.\n"
    "- change_basis: update current answer basis.\n"
    "- retrieve_rag: search indexed code/doc evidence and answer content questions.\n"
    "- compare_snapshots: compare SQL file snapshots across two or more selected branches/repositories.\n"
    "- general_chat: casual conversation.\n"
    "- clarify: ask for missing repository basis.\n\n"
    "Important planning rules:\n"
    "- If the user asks differences, comparison, functional differences, implementation differences, "
    "세부 차이, 기능 차이, 구현 차이, or 'what is different' between selected/current branches "
    "or repositories, choose compare_snapshots. This includes questions where target names are "
    "omitted but the current answer basis already contains multiple targets. Do not choose "
    "list_branches just because the word branch appears.\n"
    "- If the user asks bugs, implementation details, missing work, TODOs, unimplemented parts, "
    "priorities, or what to work on next, choose retrieve_rag.\n"
    "- For a content question, rewrite rag_query as a search-friendly Korean query that keeps "
    "the user's real goal. Include words like TODO, placeholder, 미구현, 구현, 우선순위, "
    "차이, 위험, 테스트 only when they match the user's request.\n"
    "- For pure metadata questions such as branch list or repository list, rag_query must be null.\n\n"
    "For change_basis, set basis_mode to replace/add/remove/clear. "
    "For other intents, basis_mode must be null.\n\n"
    "Output shape:\n"
    "{"
    '"intent":"rag_answer",'
    '"basis_mode":null,'
    '"tool_name":"retrieve_rag",'
    '"rag_query":"search-friendly query or null",'
    '"reason":"short reason"'
    "}"
)


@dataclass(frozen=True)
class AgentIntentPlan:
    """LLM이 고른 질문 의도와 기준 변경 모드."""

    intent: AgentIntent
    basis_mode: BasisMode | None = None
    tool_name: str | None = None
    rag_query: str | None = None
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
                tool_name=TOOL_RETRIEVE_RAG,
                rag_query=user_input.strip(),
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

    tool_name = payload.get("tool_name")
    if tool_name not in VALID_TOOL_NAMES:
        tool_name = infer_default_tool_name(intent)

    rag_query = payload.get("rag_query")
    if not isinstance(rag_query, str) or not rag_query.strip():
        rag_query = None

    reason = payload.get("reason") if isinstance(payload.get("reason"), str) else None
    return AgentIntentPlan(
        intent=intent,
        basis_mode=basis_mode,
        tool_name=tool_name,
        rag_query=rag_query,
        reason=reason,
    )


def infer_default_tool_name(intent: AgentIntent) -> str:
    """모델이 tool_name을 빠뜨렸을 때 intent에 맞는 기본 tool을 고른다."""

    return {
        INTENT_LIST_REPOSITORIES: TOOL_LIST_REPOSITORIES,
        INTENT_LIST_BRANCHES: TOOL_LIST_BRANCHES,
        INTENT_SEARCH_REPOSITORY_TARGETS: TOOL_SEARCH_REPOSITORY_TARGETS,
        INTENT_LIST_FILES: TOOL_LIST_FILES,
        INTENT_SHOW_BASIS: TOOL_SHOW_BASIS,
        INTENT_CHANGE_BASIS: TOOL_CHANGE_BASIS,
        INTENT_RAG_ANSWER: TOOL_RETRIEVE_RAG,
        INTENT_GENERAL_CHAT: TOOL_GENERAL_CHAT,
    }.get(intent, TOOL_CLARIFY)


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
