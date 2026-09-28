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
