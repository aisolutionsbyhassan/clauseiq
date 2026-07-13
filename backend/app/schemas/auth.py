"""
ClauseIQ — Auth Request/Response Schemas

Pydantic schemas for registration, login, and token responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Request Schemas
# =============================================================================

class RegisterRequest(BaseModel):
    """User registration payload."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Minimum 8 characters")
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """User login payload."""
    email: EmailStr
    password: str


# =============================================================================
# Response Schemas
# =============================================================================

class TokenResponse(BaseModel):
    """JWT token returned on successful login/registration."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile data."""
    id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Combined token + user response for registration and login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
