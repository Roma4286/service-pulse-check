from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str

class UsernameResponseSchema(BaseModel):
    username: str

class UserResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: UsernameResponseSchema

class TokenSchema(BaseModel):
    access_token: str


class TokenResponseSchema(BaseModel):
    success: bool
    message: str | None = None
    data: TokenSchema
