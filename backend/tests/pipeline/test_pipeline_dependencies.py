import pytest

from app.config import Settings
from app.pipeline.chat_models import build_chat_model
from app.pipeline.dependencies import build_llm_proposer


def test_build_llm_proposer_returns_none_when_provider_disabled() -> None:
    settings = Settings(llm_provider="none")

    assert build_llm_proposer(settings) is None


def test_build_chat_model_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="지원하지 않는 LLM provider"):
        build_chat_model("unknown", "gpt-4o-mini")
