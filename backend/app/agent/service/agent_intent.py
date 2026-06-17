from typing import Literal

INTENT_LIST_REPOSITORIES = "list_repositories"
INTENT_LIST_BRANCHES = "list_branches"
INTENT_SHOW_BASIS = "show_basis"
INTENT_CHANGE_BASIS = "change_basis"
INTENT_RAG_ANSWER = "rag_answer"
INTENT_GENERAL_CHAT = "general_chat"
INTENT_CLARIFY = "clarify"

BASIS_MODE_REPLACE = "replace"
BASIS_MODE_ADD = "add"
BASIS_MODE_REMOVE = "remove"
BASIS_MODE_CLEAR = "clear"

SHORT_REMOVE_REQUESTS = {
    "빼",
    "다시 빼",
    "이거 빼",
    "그거 빼",
    "선택 빼",
    "기준 빼",
    "기준에서 빼",
}

AgentIntent = Literal[
    "list_repositories",
    "list_branches",
    "show_basis",
    "change_basis",
    "rag_answer",
    "general_chat",
    "clarify",
]

BasisMode = Literal["replace", "add", "remove", "clear"]


def is_repository_list_question(user_input: str) -> bool:
    """사용자가 저장된 분석 레포 목록 자체를 묻는지 판별한다."""

    text = normalize_text(user_input)
    return any(
        keyword in text
        for keyword in (
            "레포 목록",
            "레포지토리 목록",
            "저장소 목록",
            "분석된 레포",
            "등록된 레포",
            "repository list",
        )
    )


def is_branch_list_question(user_input: str) -> bool:
    """특정 레포의 브랜치 메타데이터를 묻는 질문인지 판별한다."""

    text = normalize_text(user_input)
    return "브랜치" in text and any(
        keyword in text
        for keyword in ("목록", "리스트", "뭐", "어떤", "있", "없", "보여", "알려")
    )


def is_current_basis_question(user_input: str) -> bool:
    """현재 대화가 어떤 분석 결과를 기준으로 답하는지 묻는 질문인지 판별한다."""

    text = normalize_text(user_input)
    return any(
        keyword in text
        for keyword in (
            "현재 기준",
            "답변 기준",
            "선택된 레포",
            "무엇을 참고",
            "뭘 참고",
            "어떤 레포 기준",
        )
    )


def is_basis_change_request(user_input: str) -> bool:
    """앞으로 사용할 답변 기준을 바꾸라는 사용자 요청인지 판별한다."""

    text = normalize_text(user_input)
    if is_short_remove_request(user_input):
        return True

    return any(
        keyword in text
        for keyword in (
            "앞으로",
            "참고해",
            "기준으로 답",
            "기준으로 해",
            "추가해",
            "빼줘",
            "제외해",
            "제거해",
            "해제",
            "초기화",
        )
    )


def is_short_remove_request(user_input: str) -> bool:
    """대상 이름 없이 현재 답변 기준을 빼라는 짧은 명령인지 판별한다."""

    return normalize_text(user_input) in SHORT_REMOVE_REQUESTS


def is_general_chat(user_input: str) -> bool:
    """레포 분석 요청이 아니라 짧은 인사나 대화 시작에 가까운 입력인지 판별한다."""

    text = normalize_text(user_input)
    return text in {
        "야",
        "안녕",
        "하이",
        "ㅎㅇ",
        "hello",
        "hi",
        "뭐해",
        "도와줘",
    }


def detect_basis_mode(user_input: str) -> BasisMode:
    """기준 변경 요청이 교체, 추가, 제거, 초기화 중 무엇인지 결정한다."""

    text = normalize_text(user_input)
    if any(keyword in text for keyword in ("초기화", "해제", "비워", "전체 삭제", "전부 삭제")):
        return BASIS_MODE_CLEAR
    if any(keyword in text for keyword in ("빼", "제외", "빼줘")):
        return BASIS_MODE_REMOVE
    if any(keyword in text for keyword in ("추가", "도 참고", "같이 참고", "함께 참고")):
        return BASIS_MODE_ADD
    return BASIS_MODE_REPLACE


def normalize_text(value: str) -> str:
    return value.replace("*", "").replace("`", "").strip().lower()
