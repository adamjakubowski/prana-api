"""Custom exceptions for the Prana API client."""

from typing import Any


class PranaAPIError(Exception):
    """Base exception for Prana API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(PranaAPIError):
    """Raised when authentication fails."""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when the access token has expired."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when username or password is invalid."""

    pass


class UserNotActiveError(AuthenticationError):
    """Raised when user account is not active."""

    pass


class DeviceNotFoundError(PranaAPIError):
    """Raised when a device is not found."""

    pass


class RPCError(PranaAPIError):
    """Raised when an RPC command fails."""

    pass


class RateLimitError(PranaAPIError):
    """Raised when rate limit is exceeded."""

    pass


class NetworkError(PranaAPIError):
    """Raised when a network error occurs."""

    pass
