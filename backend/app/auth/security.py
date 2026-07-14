"""
ClauseIQ — Security Utilities

Password hashing (bcrypt) and JWT creation/verification.
All secrets loaded from config — never hardcoded.

Note: We use bcrypt directly instead of passlib.CryptContext because
passlib's bcrypt backend has compatibility issues with bcrypt >= 4.1.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.core.exceptions import AuthenticationError


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )



def create_access_token(subject: str) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The token subject (user ID as string).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT string.

    Returns:
        The subject (user ID) from the token payload.

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject: str | None = payload.get("sub")
        if subject is None:
            raise AuthenticationError("Invalid token: missing subject")
        return subject
    except JWTError as e:
        raise AuthenticationError(f"Invalid or expired token: {e}")
