from sqlalchemy.orm import Session

from app.agent.domain.chat import AgentTurnResult, ChatMessage, ChatSession, ChatTurn
from app.agent.service.agent_graph import AgentGraph


class GraphAgentResponder:
    """채팅 turn을 상위 AgentGraph로 넘기는 responder 어댑터."""

    def __init__(self, agent_graph: AgentGraph) -> None:
        self.agent_graph = agent_graph

    def answer(
        self,
        db: Session,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> AgentTurnResult:
        """AgentChatService가 알 필요 없는 graph 실행 세부사항을 감싼다."""

        return self.agent_graph.run(
            db=db,
            session=session,
            messages=messages,
            turn=turn,
        )
