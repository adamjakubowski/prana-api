"""Authentication handling for the Prana API client."""

import base64
import json
import time
from typing import Any

from .models import TokenPair


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT token payload without verification.

    Args:
        token: JWT token string

    Returns:
        Decoded payload as dict
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return {}

        # Decode payload (second part)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def is_token_expired(token: str, buffer_seconds: int = 60) -> bool:
    """Check if a JWT token is expired.

    Args:
        token: JWT token string
        buffer_seconds: Consider token expired this many seconds before actual expiry

    Returns:
        True if token is expired or invalid
    """
    payload = decode_jwt_payload(token)
    if not payload:
        return True

    exp = payload.get("exp")
    if not exp:
        return True

    # Check if current time is past expiration (with buffer)
    return time.time() >= (exp - buffer_seconds)


def get_token_expiry(token: str) -> int | None:
    """Get token expiration timestamp.

    Args:
        token: JWT token string

    Returns:
        Expiration timestamp or None if invalid
    """
    payload = decode_jwt_payload(token)
    return payload.get("exp")


def get_user_id_from_token(token: str) -> str | None:
    """Extract user ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID or None if not found
    """
    payload = decode_jwt_payload(token)
    return payload.get("userId")


def get_customer_id_from_token(token: str) -> str | None:
    """Extract customer ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        Customer ID or None if not found
    """
    payload = decode_jwt_payload(token)
    return payload.get("customerId")


class TokenManager:
    """Manages JWT tokens with automatic refresh capability."""

    def __init__(self, token_pair: TokenPair | None = None):
        """Initialize token manager.

        Args:
            token_pair: Initial token pair
        """
        self._token_pair = token_pair
        self._refresh_callback: callable | None = None

    @property
    def access_token(self) -> str | None:
        """Get current access token."""
        if self._token_pair:
            return self._token_pair.access_token
        return None

    @property
    def refresh_token(self) -> str | None:
        """Get current refresh token."""
        if self._token_pair:
            return self._token_pair.refresh_token
        return None

    @property
    def is_authenticated(self) -> bool:
        """Check if we have valid tokens."""
        return self._token_pair is not None and self._token_pair.access_token

    @property
    def is_access_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.access_token:
            return True
        return is_token_expired(self.access_token)

    @property
    def is_refresh_token_expired(self) -> bool:
        """Check if refresh token is expired."""
        if not self.refresh_token:
            return True
        return is_token_expired(self.refresh_token)

    def set_tokens(self, token_pair: TokenPair) -> None:
        """Set new tokens.

        Args:
            token_pair: New token pair
        """
        self._token_pair = token_pair

    def clear_tokens(self) -> None:
        """Clear all tokens."""
        self._token_pair = None

    def set_refresh_callback(self, callback: callable) -> None:
        """Set callback for token refresh.

        Args:
            callback: Async function that returns new TokenPair
        """
        self._refresh_callback = callback

    def get_authorization_header(self) -> dict[str, str]:
        """Get Authorization header dict.

        Returns:
            Dict with Authorization header or empty dict
        """
        if self.access_token:
            token_type = self._token_pair.token_type if self._token_pair else "Bearer"
            return {"Authorization": f"{token_type} {self.access_token}"}
        return {}

    def get_user_id(self) -> str | None:
        """Get user ID from current access token."""
        if self.access_token:
            return get_user_id_from_token(self.access_token)
        return None

    def get_customer_id(self) -> str | None:
        """Get customer ID from current access token."""
        if self.access_token:
            return get_customer_id_from_token(self.access_token)
        return None
