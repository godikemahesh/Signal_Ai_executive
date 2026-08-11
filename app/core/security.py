"""
Signal — Security Utilities
JWT token generation, decoding, and cryptographic utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt


def create_jwt_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=24)

    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_jwt_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None
