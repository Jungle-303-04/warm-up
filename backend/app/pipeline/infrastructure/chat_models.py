"""제공자 비종속 ChatModel 팩토리.

LangChain 채팅 모델을 환경설정으로 선택해 생성한다. import는 지연시켜
해당 제공자 패키지가 없어도 모듈 로딩이 깨지지 않게 한다.
새 제공자는 여기에 분기만 추가하면 된다(어댑터는 BaseChatModel 추상에 의존).
"""

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
