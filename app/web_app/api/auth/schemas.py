from pydantic import BaseModel


class UserLoginSchema(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    access_token: str


class TokenResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: TokenSchema
