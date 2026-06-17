from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"


@dataclass(frozen=True)
class ChatSession:
    """여러 메시지를 하나의 대화 흐름으로 묶는 최소 세션 단위."""

    id: str
    title: str | None
    created_at: datetime


@dataclass(frozen=True)
class ChatMessage:
    """사용자와 에이전트가 주고받은 내용을 저장소에 남길 때 쓰는 불변 메시지."""

    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


@dataclass(frozen=True)
class ChatTurn:
    """에이전트가 처리해야 하는 사용자 입력 한 건을 큐에 넣기 위한 작업 단위."""

    session_id: str
    user_message_id: str
    user_input: str


@dataclass(frozen=True)
class InferredRepositoryRef:
    """agent가 이번 turn에서 답변 기준으로 추론한 분석 run 정보."""

    run_id: int | None
    repository_full_name: str
    branch: str | None
    commit_sha: str | None


@dataclass(frozen=True)
class AgentTurnResult:
    """프론트에 보여줄 답변과 이번 turn의 추론 결과를 함께 담는다."""

    content: str
    inferred_repository_refs: list[InferredRepositoryRef] | None = None


class TurnQueue(Iterator[ChatTurn]):
    """채팅 입력을 순서대로 처리하고, 나중에 후속 작업을 계속 enqueue할 수 있게 한다."""

    def __init__(self) -> None:
        self._turns: deque[ChatTurn] = deque()

    def enqueue(self, turn: ChatTurn) -> None:
        """사용자 입력이나 에이전트가 만든 후속 작업을 처리 대기열 끝에 추가한다."""

        self._turns.append(turn)

    def __next__(self) -> ChatTurn:
        """대기 중인 다음 turn을 하나 꺼내 에이전트 실행기로 넘긴다."""

        if not self._turns:
            raise StopIteration
        return self._turns.popleft()


def new_chat_id() -> str:
    """DB 저장소와 메모리 저장소가 공통으로 사용할 충돌 가능성이 낮은 ID를 만든다."""

    return uuid4().hex


def now_utc() -> datetime:
    """서버 위치와 무관하게 정렬 가능한 UTC 기준 시간을 남긴다."""

    return datetime.now(timezone.utc)
