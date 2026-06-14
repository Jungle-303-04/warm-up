from threading import RLock

from app.agent.domain.chat import ChatMessage, ChatSession, new_chat_id, now_utc


class InMemoryChatStore:
    """DB 연결 전에도 채팅 흐름을 테스트할 수 있게 하는 임시 저장소."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, ChatSession] = {}
        self._messages: dict[str, list[ChatMessage]] = {}

    def create_session(self, title: str | None) -> ChatSession:
        """새 채팅방을 만들고 이후 메시지를 쌓을 빈 목록을 준비한다."""

        with self._lock:
            session = ChatSession(
                id=new_chat_id(),
                title=title,
                created_at=now_utc(),
            )
            self._sessions[session.id] = session
            self._messages[session.id] = []
            return session

    def get_session(self, session_id: str) -> ChatSession | None:
        """서비스가 채팅방 존재 여부를 확인할 수 있게 세션을 조회한다."""

        with self._lock:
            return self._sessions.get(session_id)

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        """호출자가 내부 리스트를 직접 수정하지 못하도록 메시지 복사본을 반환한다."""

        with self._lock:
            return list(self._messages.get(session_id, []))

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> ChatMessage:
        """사용자 입력과 에이전트 답변을 같은 방식으로 시간순 저장한다."""

        with self._lock:
            message = ChatMessage(
                id=new_chat_id(),
                session_id=session_id,
                role=role,
                content=content,
                created_at=now_utc(),
            )
            self._messages.setdefault(session_id, []).append(message)
            return message
