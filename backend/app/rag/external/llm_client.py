import os
from typing import Any

from openai import OpenAI

from app.shared.collections import get_list_value
from app.rag.service.ports import (
    EvidenceFormatter as EvidenceFormatterPort,
    PromptBuilder as PromptBuilderPort,
    TextGenerator,
)


DEFAULT_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
DEFAULT_SYSTEM_PROMPT = (
    "Answer in Korean. Use only the provided repository evidence. "
    "If the evidence is insufficient, say what is missing. "
    "Keep the answer practical and include citations when useful."
)
UNKNOWN_CITATION = "unknown"


class RagLlm:
    """프롬프트 생성 방식과 실제 모델 호출 방식을 조립해 RAG 답변을 만든다."""

    def __init__(
        self,
        prompt_builder: PromptBuilderPort,
        text_generator: TextGenerator,
    ) -> None:
        self.prompt_builder = prompt_builder
        self.text_generator = text_generator

    def answer_with_evidence(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> str:
        """질문과 근거 목록을 메시지로 바꾼 뒤 선택된 text generator에 위임한다."""

        messages = self.prompt_builder.build_messages(
            question=question,
            documents=documents,
            metadatas=metadatas,
        )
        return self.text_generator.generate(messages)


class PromptBuilder:
    """LLM이 레포 근거만 사용하도록 system/user 메시지 구조를 만든다."""

    def __init__(
        self,
        evidence_formatter: EvidenceFormatterPort,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.evidence_formatter = evidence_formatter
        self.system_prompt = system_prompt

    def build_messages(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> list[dict[str, str]]:
        """모델 교체와 무관하게 유지할 Chat/Responses API 입력 메시지를 만든다."""

        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self.build_user_prompt(question, documents, metadatas),
            },
        ]

    def build_user_prompt(
        self,
        question: str,
        documents: list[str],
        metadatas: list[dict],
    ) -> str:
        """질문과 citation이 붙은 evidence block을 하나의 사용자 프롬프트로 합친다."""

        evidence = self.evidence_formatter.format(documents, metadatas)
        return f"Question:\n{question.strip()}\n\nEvidence:\n{evidence}"


class EvidenceFormatter:
    """검색된 청크와 metadata를 LLM이 인용 가능한 근거 목록 텍스트로 바꾼다."""

    def format(self, documents: list[str], metadatas: list[dict]) -> str:
        """여러 근거 청크를 번호가 붙은 block으로 이어 붙인다."""

        blocks = [
            self.format_one(index, document, metadatas)
            for index, document in enumerate(documents, start=1)
        ]
        return "\n\n".join(blocks)

    def format_one(
        self,
        index: int,
        document: str,
        metadatas: list[dict],
    ) -> str:
        """청크 하나에 citation을 붙여 답변 근거로 추적 가능하게 만든다."""

        metadata = get_list_value(metadatas, index - 1, {}) or {}
        citation = metadata.get("citation", UNKNOWN_CITATION)
        return f"[{index}] citation={citation}\n{document.strip()}"


class OpenAIGenerator:
    """OpenAI Responses API 호출을 감싸 다른 LLM provider로 교체하기 쉽게 한다."""

    def __init__(self, model: str = DEFAULT_LLM_MODEL) -> None:
        self.model = model
        self.client = OpenAI()

    def generate(self, messages: list[dict[str, Any]]) -> str:
        """조립된 메시지를 모델에 보내고 화면에 표시할 텍스트만 반환한다."""

        response = self.client.responses.create(
            model=self.model,
            input=messages,
        )
        return response.output_text.strip()
