from pydantic import BaseModel


class WebhookAcceptedResponse(BaseModel):
    status: str
    event: str | None = None
    repository: str | None = None
    branch: str | None = None


class PublishProposalRequest(BaseModel):
    issue_number: int


class PublishProposalResponse(BaseModel):
    comment_url: str
