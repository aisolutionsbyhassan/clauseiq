"""
ClauseIQ — Auth Service

Business logic for user registration and authentication.
Services raise domain exceptions; they never raise HTTPException.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import AuthenticationError, DuplicateResourceError
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.auth import AuthResponse, RegisterRequest, UserResponse

logger = get_logger("auth_service")


async def register_user(data: RegisterRequest, db: AsyncSession) -> AuthResponse:
    """
    Register a new user account.

    Raises:
        DuplicateResourceError: If a user with this email already exists.
    """
    # Check for existing user
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise DuplicateResourceError(f"A user with email '{data.email}' already exists")

    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()  # Assign ID before creating token
    await db.refresh(user)

    logger.info("User registered: user_id=%s, email=%s", user.id, user.email)

    # Generate token
    access_token = create_access_token(subject=str(user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


async def authenticate_user(email: str, password: str, db: AsyncSession) -> AuthResponse:
    """
    Authenticate a user by email and password.

    Raises:
        AuthenticationError: If credentials are invalid.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    logger.info("User authenticated: user_id=%s", user.id)

    access_token = create_access_token(subject=str(user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
