from pydantic import BaseModel, ConfigDict


class GitHubOAuthLoginResponseDTO(BaseModel):
    authorize_url: str
    state: str
    scope: str


class AuthenticatedUserDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    github_user_id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class AuthTokenResponseDTO(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthenticatedUserDTO


class AuthMeResponseDTO(BaseModel):
    user: AuthenticatedUserDTO
