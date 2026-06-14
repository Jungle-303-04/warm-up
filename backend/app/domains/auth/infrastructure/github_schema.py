from pydantic import BaseModel, ConfigDict


class GitHubOAuthTokenDTO(BaseModel):
    access_token: str
    token_type: str
    scope: str | None = None
    expires_in: int | None = None


class GitHubUserProfileDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class GitHubEmailDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    primary: bool = False
    verified: bool = False
