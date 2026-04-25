"""
Auth schemas – registration, login, token responses.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthCallback(BaseModel):
    code: str
    state: str | None = None


class AuthResponse(BaseModel):
    success: bool = True
    message: str
    data: TokenResponse | None = None
