from app.agent.domain.chat import ChatMessage, ChatSession, ChatTurn

DEFAULT_AGENT_PREFIX = "Agent placeholder response"


class EchoAgentResponder:
    """실제 LLM 에이전트가 붙기 전까지 채팅 큐와 API 흐름을 검증하는 대체 응답기."""

    def answer(
        self,
        session: ChatSession,
        messages: list[ChatMessage],
        turn: ChatTurn,
    ) -> str:
        """입력 내용이 응답까지 전달되는지 확인할 수 있게 그대로 되돌려준다."""

        return f"{DEFAULT_AGENT_PREFIX}: {turn.user_input}"
