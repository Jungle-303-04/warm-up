from pydantic import BaseModel


class WebhookAcceptedResponse(BaseModel):
    status: str
    event: str | None = None
    repository: str | None = None
    branch: str | None = None
