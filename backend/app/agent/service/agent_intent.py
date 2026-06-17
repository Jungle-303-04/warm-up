import re
from typing import Literal

INTENT_LIST_REPOSITORIES = "list_repositories"
INTENT_LIST_BRANCHES = "list_branches"
INTENT_LIST_FILES = "list_files"
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
KOREAN_SHORTHAND_EXPANSIONS = (
    ("ㄹㅍㅁㄹ", "레포 목록"),
    ("ㄿㅁㄹ", "레포 목록"),
    ("ㄹㅍ", "레포"),
    ("ㄿ", "레포"),
    ("ㅂㄹㅊ", "브랜치"),
    ("ㅁㄹ", "목록"),
)
KOREAN_PATH_HINTS = (
    "백엔드",
    "프론트엔드",
    "프론트",
    "앱",
    "어스",
    "인증",
)
PATH_REQUEST_KEYWORDS = (
    "안에",
    "아래",
    "있는",
    "전부",
    "전체",
    "달라",
    "줘",
    "꺼",
    "것",
)
ASCII_PATH_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_.-]+")
TARGET_SELECTION_BLOCKERS = (
    "?",
    "뭐",
    "무엇",
    "무슨",
    "어떤",
    "어디",
    "어떻게",
    "왜",
    "누구",
    "목록",
    "리스트",
    "브랜치",
    "레포",
    "레포지토리",
    "저장소",
    "파일",
    "폴더",
    "디렉토리",
    "구조",
    "트리",
    "버그",
    "오류",
    "문제",
    "설명",
    "보여",
    "알려",
    "달라",
    "줘",
    "있는",
    "안에",
    "아래",
    "야",
    "안녕",
    "하이",
    "ㅎㅇ",
    "욜",
)
MIN_BARE_TARGET_TOKENS = 2
MAX_BARE_TARGET_TOKENS = 5

AgentIntent = Literal[
    "list_repositories",
    "list_branches",
    "list_files",
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
    if "브랜치" not in text:
        return False

    return has_digit(text) or any(
        keyword in text
        for keyword in ("목록", "리스트", "뭐", "어떤", "있", "없", "보여", "알려")
    )


def is_file_list_question(user_input: str) -> bool:
    """파일, 폴더, 디렉토리 구조처럼 SQL path 목록으로 답해야 하는 질문인지 본다."""

    text = normalize_text(user_input)
    if has_path_expression(text) and any(
        keyword in text for keyword in PATH_REQUEST_KEYWORDS
    ):
        return True

    return any(
        keyword in text
        for keyword in (
            "파일",
            "폴더",
            "디렉토리",
            "구조",
            "트리",
            "domain",
            "도메인",
        )
    ) and any(
        keyword in text
        for keyword in ("목록", "뭐", "무엇", "어떤", "있", "보여", "알려", "구성")
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
            "빼",
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


def is_bare_target_selection(user_input: str) -> bool:
    """짧은 레포/브랜치 이름 나열처럼 질문이 아니라 기준 선택에 가까운 입력인지 본다."""

    text = normalize_text(user_input)
    if not text or any(keyword in text for keyword in TARGET_SELECTION_BLOCKERS):
        return False

    tokens = [token for token in text.replace("/", " ").replace("\\", " ").split() if token]
    return MIN_BARE_TARGET_TOKENS <= len(tokens) <= MAX_BARE_TARGET_TOKENS


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
    text = value.replace("*", "").replace("`", "").strip().lower()
    for shorthand, expanded in KOREAN_SHORTHAND_EXPANSIONS:
        text = text.replace(shorthand, expanded)
    return text


def has_digit(value: str) -> bool:
    return any(char.isdigit() for char in value)


def has_path_expression(text: str) -> bool:
    if "/" in text or "\\" in text:
        return True

    hint_count = sum(1 for hint in KOREAN_PATH_HINTS if hint in text)
    return hint_count >= 2


def has_path_focus_hint(user_input: str) -> bool:
    """전체 파일/폴더 목록이 아니라 특정 경로를 좁혀 말한 요청인지 본다."""

    text = normalize_text(user_input)
    if "/" in text or "\\" in text:
        return True
    if any(hint in text for hint in KOREAN_PATH_HINTS):
        return True
    return bool(ASCII_PATH_TOKEN_PATTERN.search(text)) and any(
        keyword in text for keyword in PATH_REQUEST_KEYWORDS
    )
