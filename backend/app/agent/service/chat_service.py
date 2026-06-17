from app.agent.api.schema import (
    AgentInferredRepositoryRefDTO,
    ChatMessageDTO,
    ChatSendMessageRequestDTO,
    ChatSendMessageResponseDTO,
    ChatSessionCreateRequestDTO,
    ChatSessionDTO,
    ChatSessionDetailResponseDTO,
)
from app.agent.domain.chat import (
    ASSISTANT_ROLE,
    USER_ROLE,
    AgentTurnResult,
    ChatSession,
    ChatTurn,
    InferredRepositoryRef,
    TurnQueue,
)
from app.agent.service.ports import AgentResponder, ChatStore
from sqlalchemy.orm import Session


class AgentChatService:
    """채팅 세션 저장, 입력 큐 처리, 에이전트 응답 저장을 한 흐름으로 조율한다."""

    def __init__(
        self,
        store: ChatStore,
        responder: AgentResponder,
    ) -> None:
        self.store = store
        self.responder = responder

    def create_session(
        self,
        request: ChatSessionCreateRequestDTO,
    ) -> ChatSessionDetailResponseDTO:
        """첫 메시지 없이 대화 공간만 열어 프론트가 채팅 화면을 먼저 구성하게 한다."""

        session = self.store.create_session(request.title)
        return build_session_detail(session, [])

    def get_session_detail(self, session_id: str) -> ChatSessionDetailResponseDTO:
        """화면 새로고침이나 채팅방 재진입 때 현재 세션과 누적 메시지를 복원한다."""

        session = self.require_session(session_id)
        return build_session_detail(session, self.store.list_messages(session_id))

    def send_message(
        self,
        db: Session,
        session_id: str,
        request: ChatSendMessageRequestDTO,
    ) -> ChatSendMessageResponseDTO:
        """사용자 입력을 저장한 뒤 turn 큐로 넘겨 에이전트 응답까지 한 번 처리한다."""

        session = self.require_session(session_id)
        user_message = self.store.append_message(
            session_id=session.id,
            role=USER_ROLE,
            content=request.content,
        )

        queue = TurnQueue()
        queue.enqueue(
            ChatTurn(
                session_id=session.id,
                user_message_id=user_message.id,
                user_input=user_message.content,
            )
        )
        processed_turns, turn_result = self.run_queue(db, session, queue)

        return ChatSendMessageResponseDTO(
            session=to_session_dto(session),
            messages=to_message_dtos(self.store.list_messages(session.id)),
            processed_turns=processed_turns,
            inferred_repository_refs=to_inferred_repository_ref_dtos(
                turn_result.inferred_repository_refs if turn_result else None
            ),
        )

    def run_queue(
        self,
        db: Session,
        session: ChatSession,
        queue: TurnQueue,
    ) -> tuple[int, AgentTurnResult | None]:
        """큐에 쌓인 turn을 순서대로 실행해 향후 다단계 에이전트 작업을 수용한다."""

        processed_turns = 0
        last_turn_result: AgentTurnResult | None = None
        for turn in queue:
            turn_result = self.responder.answer(
                db=db,
                session=session,
                messages=self.store.list_messages(session.id),
                turn=turn,
            )
            self.store.append_message(
                session_id=session.id,
                role=ASSISTANT_ROLE,
                content=turn_result.content,
            )
            processed_turns += 1
            last_turn_result = turn_result
        return processed_turns, last_turn_result

    def require_session(self, session_id: str) -> ChatSession:
        """존재하지 않는 채팅방에 메시지가 쌓이지 않도록 세션 존재를 보장한다."""

        session = self.store.get_session(session_id)
        if session is None:
            raise ValueError("chat session not found")
        return session


def build_session_detail(
    session: ChatSession,
    messages: list,
) -> ChatSessionDetailResponseDTO:
    """세션과 메시지 목록을 API 응답 형태로 묶어 라우터의 변환 코드를 줄인다."""

    return ChatSessionDetailResponseDTO(
        session=to_session_dto(session),
        messages=to_message_dtos(messages),
    )


def to_session_dto(session: ChatSession) -> ChatSessionDTO:
    """도메인 세션 객체를 외부 응답 DTO로 변환한다."""

    return ChatSessionDTO(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
    )


def to_message_dtos(messages: list) -> list[ChatMessageDTO]:
    """저장소 메시지 목록을 프론트가 바로 렌더링할 수 있는 DTO 목록으로 바꾼다."""

    return [
        ChatMessageDTO(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        for message in messages
    ]


def to_inferred_repository_ref_dtos(
    refs: list[InferredRepositoryRef] | None,
) -> list[AgentInferredRepositoryRefDTO] | None:
    """이번 turn에서 추론한 답변 대상이 없으면 JSON null로 내려준다."""

    if not refs:
        return None

    return [
        AgentInferredRepositoryRefDTO(
            run_id=ref.run_id,
            repository_full_name=ref.repository_full_name,
            branch=ref.branch,
            commit_sha=ref.commit_sha,
        )
        for ref in refs
    ]
