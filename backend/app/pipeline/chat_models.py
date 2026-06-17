"""제공자 비종속 ChatModel 팩토리."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

OPENAI = "openai"
SUPPORTED_PROVIDERS = (OPENAI,)


def build_chat_model(
    provider: str,
    model: str,
    api_key: str | None = None,
    *,
    temperature: float = 0.0,
) -> BaseChatModel:
    if provider == OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=api_key, temperature=temperature)  # type: ignore

    raise ValueError(
        f"지원하지 않는 LLM provider: {provider!r} (가능: {', '.join(SUPPORTED_PROVIDERS)})"
    )
