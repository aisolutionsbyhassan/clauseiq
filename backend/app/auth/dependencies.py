"""
ClauseIQ — FastAPI Auth Dependencies

Provides `get_current_user` — the single authorization choke point
referenced in AGENT.md Section 6.7 and Section 18 (future RBAC extension).
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.core.exceptions import AuthenticationError
from app.database import get_db
from app.models.user import User

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT from the
    Authorization header, then loads and returns the corresponding User.

    Raises:
        AuthenticationError: If the token is invalid or the user doesn't exist.
    """
    token = credentials.credentials
    user_id_str = decode_access_token(token)

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid token: malformed user ID")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User associated with this token no longer exists")

    return user
