from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip: str = Field(..., max_length=45)


class RegisterResponse(BaseModel):
    id: str
