from typing import Any

from langchain_openai import ChatOpenAI

from app.agent.external.text_generator import DEFAULT_AGENT_LLM_MODEL


class LangChainToolCallingLlm:
    """LangChain tool calling 모델 호출을 agent 내부 계약에 맞게 감싼다."""

    def __init__(self, model: str = DEFAULT_AGENT_LLM_MODEL) -> None:
        self.model = ChatOpenAI(model=model)

    def invoke(self, messages: list[Any], tools: list[Any]) -> Any:
        """현재 대화 메시지와 사용 가능한 tool 목록을 모델에 넘긴다."""

        if tools:
            return self.model.bind_tools(tools).invoke(messages)

        return self.model.invoke(messages)
