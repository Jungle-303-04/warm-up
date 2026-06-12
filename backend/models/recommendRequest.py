from sqlmodel import SQLModel

class RecommendRequest(SQLModel):
    text: str
    preferred_tone: str | None = None


