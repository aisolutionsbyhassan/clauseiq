"""
ClauseIQ — Auth Router

Handles HTTP concerns for user registration and login.
Business logic is delegated to auth_service per AGENT.md Section 11.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import authenticate_user, register_user
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user account and return a JWT."""
    return await register_user(data=data, db=db)


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Authenticate with email/password and return a JWT."""
    return await authenticate_user(
        email=data.email,
        password=data.password,
        db=db,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
