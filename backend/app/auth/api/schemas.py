from pydantic import BaseModel


class MeResponse(BaseModel):
    user_id: int
    login: str
