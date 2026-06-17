from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.pipeline.router import CodeReference, RetrievalChunk
from app.pipeline.domain import VERIFIED
from app.pipeline.proposer import LangGraphProposer


def _fake_model(payload: str) -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter([AIMessage(content=payload)]))


def _reference() -> CodeReference:
    return CodeReference(
        id="app.py:login",
        path="app.py",
        symbol="login",
        line=1,
        commit_sha="abc123",
        status=VERIFIED,
    )


def test_generate_returns_empty_without_references() -> None:
    proposer = LangGraphProposer(chat_model=_fake_model('{"proposals": []}'))

    assert proposer.generate([], []) == []


def test_generate_parses_llm_json_into_drafts() -> None:
    payload = (
        '{"proposals": [{"target_path": "app.py", '
        '"proposed_change": "문서에 login 흐름을 추가하세요.", "confidence": 0.8}]}'
    )
    proposer = LangGraphProposer(chat_model=_fake_model(payload))

    drafts = proposer.generate([_reference()], [])

    assert len(drafts) == 1
    assert drafts[0].target_path == "app.py"
    assert drafts[0].confidence == 0.8


def test_generate_attaches_evidence_by_matching_source_path() -> None:
    payload = (
        '{"proposals": [{"target_path": "app.py", '
        '"proposed_change": "링크하세요.", "confidence": 0.6}]}'
    )
    chunks = [
        RetrievalChunk(
            id="app.py@abc123",
            source_path="app.py",
            text="def login(): pass",
            citation="repo:app.py@abc123",
        )
    ]
    proposer = LangGraphProposer(chat_model=_fake_model(payload))

    drafts = proposer.generate([_reference()], chunks)

    assert drafts[0].evidence == ["repo:app.py@abc123"]
