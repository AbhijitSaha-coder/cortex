from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")


class UserRegister(BaseModel):
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password with minimum 8 characters")
    full_name: Optional[str] = Field(None, max_length=100)

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()



class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
