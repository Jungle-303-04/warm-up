from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatSessionCreateRequestDTO(BaseModel):
    title: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        title = value.strip()
        return title or None


class ChatSendMessageRequestDTO(BaseModel):
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("content must not be empty")
        return content


class ChatSessionDTO(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime


class ChatMessageDTO(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class ChatSessionDetailResponseDTO(BaseModel):
    session: ChatSessionDTO
    messages: list[ChatMessageDTO]


class AgentInferredRepositoryRefDTO(BaseModel):
    run_id: int | None = None
    repository_full_name: str
    branch: str | None = None
    commit_sha: str | None = None


class ChatSendMessageResponseDTO(ChatSessionDetailResponseDTO):
    processed_turns: int
    inferred_repository_refs: list[AgentInferredRepositoryRefDTO] | None = None
