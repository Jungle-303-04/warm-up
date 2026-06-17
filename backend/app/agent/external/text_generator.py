import os
from typing import Any

from openai import OpenAI


DEFAULT_AGENT_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")


class OpenAITextGenerator:
    """agent planner가 쓰는 OpenAI Responses API text generator."""

    def __init__(self, model: str = DEFAULT_AGENT_LLM_MODEL) -> None:
        self.model = model
        self.client = OpenAI()

    def generate(self, messages: list[dict[str, Any]]) -> str:
        """조립된 메시지를 모델에 보내고 텍스트 응답만 반환한다."""

        response = self.client.responses.create(
            model=self.model,
            input=messages,
        )
        return response.output_text.strip()
